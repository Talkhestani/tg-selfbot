"""Proxy list loader and auto-creation."""

from __future__ import annotations

from pathlib import Path

PROXY_FILE = Path.home() / ".config" / "tgself" / "proxies.txt"
KNOWN_TYPES = {"socks5", "socks4", "http", "mtproto"}


def ensure_proxy_file() -> Path:
    PROXY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not PROXY_FILE.exists():
        PROXY_FILE.write_text("")
    return PROXY_FILE


def load_proxies() -> list[str]:
    p = ensure_proxy_file()
    lines = p.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def first_proxy_dict() -> dict | None:
    proxies = load_proxies()
    for line in proxies:
        try:
            parts = line.split()
            if len(parts) == 2 and parts[0] in KNOWN_TYPES:
                proxy_type = parts[0]
                rest = parts[1]
            elif len(parts) == 1:
                proxy_type = "socks5"
                rest = parts[0]
            else:
                continue
            host, port = rest.rsplit(":", 1)
            result = {
                "proxy_type": proxy_type,
                "addr": host,
                "port": int(port),
                "rdns": True,
            }
            if proxy_type == "mtproto":
                # mtproto usually needs secret but telethon accepts basic dict
                result["secret"] = None  # user can extend if needed
            return result
        except Exception:
            continue
    return None
