"""SSRF validation tests."""

from __future__ import annotations

import pytest

from selfbot.utils.ssrf import (
    SSRFBlockedError,
    SSRFResult,
    parse_url,
    validate_ssrf,
)

PRIVATE_TARGETS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8080/admin",
    "http://10.0.0.1",
    "http://172.16.0.1",
    "http://192.168.1.1",
    "http://169.254.169.254/latest/meta-data",
    "https://0.0.0.0",
    "http://[::1]",
    "http://[::ffff:127.0.0.1]",
    "http://192.0.0.1",  # IETF protocol assignments
]


@pytest.mark.parametrize("url", PRIVATE_TARGETS)
def test_private_targets_are_blocked(url: str) -> None:
    with pytest.raises(SSRFBlockedError):
        validate_ssrf(url, resolve=False)


def test_metadata_hostnames_are_blocked() -> None:
    for host in ("metadata.google.internal", "metadata.google", "metadata"):
        with pytest.raises(SSRFBlockedError):
            validate_ssrf(f"http://{host}/", resolve=False)


def test_internal_suffixes_are_blocked() -> None:
    for host in ("server.internal", "db.local", "api.internal", "intra.grp.local"):
        with pytest.raises(SSRFBlockedError):
            validate_ssrf(f"https://{host}/", resolve=False)


def test_unsupported_scheme() -> None:
    with pytest.raises(ValueError):
        validate_ssrf("file:///etc/passwd", resolve=False)
    with pytest.raises(ValueError):
        validate_ssrf("ftp://example.com/x", resolve=False)


def test_missing_hostname() -> None:
    with pytest.raises(ValueError):
        parse_url("http:///")


def test_public_ip_is_allowed() -> None:
    result, port = validate_ssrf("https://8.8.8.8/", resolve=False)
    assert isinstance(result, SSRFResult)
    assert result.ip == "8.8.8.8"
    assert result.use_tls is True
    assert port == 443


def test_cgnat_is_blocked() -> None:
    """100.64.0.0/10 (carrier-grade NAT) must never be reached."""
    with pytest.raises(SSRFBlockedError):
        validate_ssrf("http://100.64.0.1", resolve=False)


def test_public_hostname_allows_without_resolution() -> None:
    result, port = validate_ssrf("https://example.com/path", resolve=False)
    assert result.hostname == "example.com"
    assert result.use_tls is True
    assert port == 443


def test_default_http_port() -> None:
    _, port = validate_ssrf("http://example.com", resolve=False)
    assert port == 80


def test_explicit_port() -> None:
    _, port = validate_ssrf("http://example.com:8080/x", resolve=False)
    assert port == 8080


def test_localhost_resolves_to_private_ip() -> None:
    """Hostnames resolving to private addresses must be blocked."""
    with pytest.raises(SSRFBlockedError):
        validate_ssrf("http://localhost", resolve=True)
