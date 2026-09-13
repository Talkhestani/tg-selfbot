"""Network diagnostic tools with strict SSRF protection."""

from __future__ import annotations

import asyncio
import logging
import socket
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
import whois
from dns import resolver as dns_resolver
from dns import reversename as dns_reversename

from selfbot.utils.ssrf import SSRFBlockedError, SSRFResult, validate_ssrf

logger = logging.getLogger(__name__)

RESOLVE_TIMEOUT = 8.0
HTTP_TIMEOUT = 15.0
SSL_TIMEOUT = 10.0


@dataclass
class NetworkError(Exception):
    """A user-friendly network error."""

    message: str


@dataclass
class PingResult:
    host: str
    ip: str
    sent: int = 0
    received: int = 0
    rtts: list[float] = field(default_factory=list)
    error: str | None = None

    @property
    def loss_percent(self) -> float:
        if self.sent == 0:
            return 0.0
        return (self.sent - self.received) / self.sent * 100


def _ping_sync(host: str, port: int, count: int, timeout: float, result: PingResult) -> PingResult:
    """Blocking TCP-connect ping loop, run via ``asyncio.to_thread``."""
    for attempt in range(count):
        result.sent += 1
        started = time.monotonic()
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.close()
            elapsed = (time.monotonic() - started) * 1000
            result.received += 1
            result.rtts.append(round(elapsed, 1))
            if not result.ip:
                result.ip = socket.gethostbyname(host)
        except (OSError, UnicodeError) as exc:
            logger.debug("ping attempt %d to %s failed: %s", attempt, host, exc)
            if attempt == count - 1:
                result.error = str(exc)
            time.sleep(0.2)
    return result


class NetworkService:
    """Runs network diagnostics against remote hosts.

    Every user-supplied destination goes through SSRF validation first.
    """

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=HTTP_TIMEOUT, follow_redirects=False)

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _ssrf_or_raise(host_or_url: str) -> tuple[SSRFResult, int]:
        try:
            return validate_ssrf(host_or_url)
        except (SSRFBlockedError, ValueError) as exc:
            raise NetworkError(str(exc)) from exc

    async def _safe_request(self, url: str) -> httpx.Response:
        validate_ssrf(url)
        try:
            response = await self._client.get(url)
        except httpx.TimeoutException as exc:
            raise NetworkError("پاسخ از مقصد دریافت نشد (timeout)") from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"درخواست ناموفق بود: {exc.__class__.__name__}") from exc
        response.raise_for_status()
        return response

    # -- ping -------------------------------------------------------------
    async def ping(self, host: str, count: int = 4, timeout_secs: float = 4.0) -> PingResult:
        host = host.strip().lower().rstrip(".")
        result = PingResult(host=host, ip="")
        try:
            _, port = self._ssrf_or_raise(f"https://{host}")
        except NetworkError as exc:
            result.error = exc.message
            return result

        return await asyncio.to_thread(_ping_sync, host, port, count, timeout_secs, result)

    # -- DNS --------------------------------------------------------------
    async def dns_lookup(self, host: str, record_type: str = "A") -> list[str]:
        host = host.strip().lower().rstrip(".")
        self._ssrf_or_raise(f"https://{host}")
        try:
            # PTR queries must be reverse-form (in-addr.arpa / ip6.arpa);
            # dnspython does not convert a bare address for us.
            query_name: Any = (
                dns_reversename.from_address(host) if record_type == "PTR" else host
            )
            answers = dns_resolver.resolve(query_name, record_type, lifetime=RESOLVE_TIMEOUT)
            return [answer.to_text() for answer in answers]
        except dns_resolver.NoAnswer:
            return []
        except (
            dns_resolver.NXDOMAIN,
            dns_resolver.NoNameservers,
            dns_resolver.LifetimeTimeout,
            Exception,
        ) as exc:
            raise NetworkError(f"پاسخ DNS دریافت نشد: {exc.__class__.__name__}") from exc

    async def ip_lookup(self, target: str) -> dict[str, str]:
        target = target.strip().lower().rstrip(".")
        # If it's a bare IP, show it directly with reverse-dns info.
        try:
            ip_address = socket.gethostbyname(target)
        except socket.gaierror as exc:
            raise NetworkError("نام میزبان یا آدرس IP پیدا نشد") from exc
        info = {"ip": ip_address, "hostname": target}
        try:
            reverse_names = await self.dns_lookup(ip_address, "PTR")
            info["reverse"] = reverse_names[0] if reverse_names else target
        except NetworkError:
            info["reverse"] = target
        return info

    # -- WHOIS ------------------------------------------------------------
    async def whois(self, domain: str) -> str:
        domain = domain.strip().lower().rstrip(".")
        self._ssrf_or_raise(f"https://{domain}")
        try:
            # python-whois performs blocking socket queries; keep it out of the loop.
            response = await asyncio.to_thread(whois.whois, domain)
        except Exception as exc:
            raise NetworkError(f"اطلاعات WHOIS دریافت نشد: {exc.__class__.__name__}") from exc

        fields: list[tuple[str, Any]] = [
            ("domain_name", response.domain_name),
            ("registrar", response.registrar),
            ("creation_date", response.creation_date),
            ("expiration_date", response.expiration_date),
            ("updated_date", response.updated_date),
            ("name_servers", response.name_servers),
            ("status", response.status),
            ("emails", response.emails),
            ("org", response.org),
            ("country", response.country),
        ]
        lines: list[str] = []
        for key, value in fields:
            if not value:
                continue
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value[:5])
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    # -- HTTP status ------------------------------------------------------
    async def status_url(self, url: str) -> dict[str, Any]:
        validate_ssrf(url)
        try:
            response = await self._client.get(url, follow_redirects=False)
        except httpx.TimeoutException as exc:
            raise NetworkError("پاسخ از مقصد دریافت نشد (timeout)") from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"درخواست ناموفق بود: {exc.__class__.__name__}") from exc
        return {
            "status_code": response.status_code,
            "reason": response.reason_phrase,
            "headers": dict(response.headers),
        }

    async def uptime(self, url: str, attempts: int = 3) -> dict[str, Any]:
        validate_ssrf(url)
        success = 0
        failures = 0
        first_error: str | None = None
        for _ in range(attempts):
            try:
                response = await self._client.get(url, follow_redirects=False)
                if response.status_code < 500:
                    success += 1
                elif first_error is None:
                    first_error = f"HTTP {response.status_code}"
            except httpx.RequestError as exc:
                failures += 1
                if first_error is None:
                    first_error = exc.__class__.__name__
        return {"success": success, "failures": failures, "error": first_error}

    # -- SSL --------------------------------------------------------------
    @staticmethod
    def _ssl_cert_sync(host: str) -> dict[str, Any] | None:
        """Fetch a peer certificate; blocking, so run via ``asyncio.to_thread``."""
        context = ssl.create_default_context()
        with (
            socket.create_connection((host, 443), timeout=SSL_TIMEOUT) as sock,
            context.wrap_socket(sock, server_hostname=host) as tls,
        ):
            return tls.getpeercert()

    async def ssl_info(self, host: str) -> dict[str, Any]:
        host = host.strip().lower().rstrip(".")
        self._ssrf_or_raise(f"https://{host}")
        try:
            cert = await asyncio.to_thread(self._ssl_cert_sync, host)
        except (ssl.SSLError, ssl.CertificateError, OSError, ValueError) as exc:
            raise NetworkError(f"گواهی SSL دریافت نشد: {exc}") from exc

        def _format_date(value: Any) -> str:
            if not isinstance(value, str):
                return ""
            try:
                return datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").astimezone().isoformat()
            except (ValueError, OSError, TypeError):
                return value

        if not cert:
            return {
                "subject": host,
                "issuer": "",
                "not_before": "",
                "not_after": "",
                "serial": "",
                "version": "",
            }
        raw_subject: Any = cert.get("subject", [])
        raw_issuer: Any = cert.get("issuer", [])
        subject = {str(pair[0][0]): str(pair[0][1]) for pair in raw_subject}
        issuer = {str(pair[0][0]): str(pair[0][1]) for pair in raw_issuer}
        return {
            "subject": subject.get("commonName", host),
            "issuer": issuer.get("commonName", ""),
            "not_before": _format_date(cert.get("notBefore")),
            "not_after": _format_date(cert.get("notAfter")),
            "serial": str(cert.get("serialNumber", "")),
            "version": str(cert.get("version", "")),
        }

    # -- Headers ----------------------------------------------------------
    async def fetch_headers(self, url: str) -> dict[str, str]:
        validate_ssrf(url)
        try:
            response = await self._client.head(url, follow_redirects=False)
        except httpx.TimeoutException as exc:
            raise NetworkError("پاسخ از مقصد دریافت نشد (timeout)") from exc
        except httpx.RequestError as exc:
            raise NetworkError(f"درخواست ناموفق بود: {exc.__class__.__name__}") from exc
        return dict(response.headers)
