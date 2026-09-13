"""SSRF protection: reject requests to internal / sensitive destinations."""

from __future__ import annotations

import ipaddress
import logging
import socket
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Cloud metadata endpoints (and similar link-local services) that must never
# be reached through user-supplied URLs/hostnames.
BLOCKED_HOSTNAMES: dict[str, str] = {
    "169.254.169.254": "cloud metadata",
    "metadata.google.internal": "cloud metadata",
    "metadata.google": "cloud metadata",
    "metadata": "cloud metadata",
}

BLOCKED_HOST_SUFFIXES = (
    ".internal",
    ".local",
)


class SSRFBlockedError(Exception):
    """Raised when a destination is blocked by SSRF protection."""


@dataclass(frozen=True)
class SSRFResult:
    """Result of a safe destination resolution."""

    hostname: str
    ip: str
    use_tls: bool


def _is_private(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Broad check first: anything not globally reachable (loopback, RFC1918,
    # CGNAT 100.64/10, documentation ranges, benchmarking, etc.) is off-limits.
    if isinstance(ip, ipaddress.IPv4Address):
        if not ip.is_global:
            return True
        return ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified
    if isinstance(ip, ipaddress.IPv6Address):
        if not ip.is_global and not ip.is_reserved and not ip.is_site_local:
            return True
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or ip.is_site_local
        )


def parse_url(url: str) -> tuple[str, str, int]:
    """Parse an http/https URL, returning (hostname, scheme, port).

    Raises ValueError for unsupported schemes or malformed URLs.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url if "://" in url else f"http://{url}")
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported scheme: {parsed.scheme!r}")
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("missing hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return hostname, parsed.scheme, port


def validate_ssrf(url: str, *, resolve: bool = True) -> tuple[SSRFResult, int]:
    """Validate a URL for SSRF safety.

    Returns (SSRFResult, port). Raises SSRFBlockedError / ValueError.
    """
    hostname, scheme, port = parse_url(url)
    lowered = hostname.lower().rstrip(".")

    if lowered in BLOCKED_HOSTNAMES:
        raise SSRFBlockedError(f"blocked hostname: {lowered}")

    for suffix in BLOCKED_HOST_SUFFIXES:
        if lowered.endswith(suffix):
            raise SSRFBlockedError(f"blocked internal hostname: {lowered}")

    # Direct IP addresses
    try:
        ip_obj = ipaddress.ip_address(hostname)
    except ValueError:
        ip_obj = None

    if ip_obj is not None:
        if _is_private(ip_obj):
            raise SSRFBlockedError(f"blocked private/loopback address: {hostname}")
        return SSRFResult(hostname=hostname, ip=str(ip_obj), use_tls=scheme == "https"), port

    if not resolve:
        return SSRFResult(hostname=hostname, ip="", use_tls=scheme == "https"), port

    # Resolve hostname via /etc/hosts aware query; Telethon client is unrelated.
    try:
        infos = socket.getaddrinfo(
            hostname, port, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise ValueError(f"could not resolve {hostname}") from exc

    seen: set[str] = set()
    for info in infos:
        raw_ip = str(info[4][0]).split("%")[0]
        if raw_ip in seen:
            continue
        seen.add(raw_ip)
        try:
            ip_obj = ipaddress.ip_address(raw_ip)
            if _is_private(ip_obj):
                logger.warning("blocked private resolution %s -> %s", hostname, raw_ip)
                raise SSRFBlockedError(f"blocked private address for {hostname}: {raw_ip}")
        except ValueError:
            continue

    if not seen:
        raise ValueError(f"could not resolve {hostname}")

    first_ip = str(infos[0][4][0])
    return SSRFResult(hostname=hostname, ip=first_ip, use_tls=scheme == "https"), port
