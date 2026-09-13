"""Password and random-value generators."""

from __future__ import annotations

import secrets
import string

PASSWORD_MIN = 8
PASSWORD_MAX = 64


def generate_password(
    length: int = 20,
    *,
    uppercase: bool = True,
    lowercase: bool = True,
    digits: bool = True,
    symbols: bool = True,
) -> str:
    """Generate a cryptographically random password using secrets."""
    length = max(PASSWORD_MIN, min(length, PASSWORD_MAX))
    pools: list[str] = []
    if uppercase:
        pools.append(string.ascii_uppercase)
    if lowercase:
        pools.append(string.ascii_lowercase)
    if digits:
        pools.append(string.digits)
    if symbols:
        pools.append("!@#$%^&*()-_=+[]{};:,.<>?")
    if not pools:
        pools.append(string.ascii_letters)

    all_chars = "".join(pools)
    password = [secrets.choice(pool) for pool in pools]
    while len(password) < length:
        password.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def random_int(start: int, end: int) -> int:
    """Return a cryptographically-random integer within [start, end]."""
    return secrets.randbelow(end - start + 1) + start


def random_choice(options: list[str]) -> str:
    """Return a random item from a list using secrets."""
    return secrets.choice(options)
