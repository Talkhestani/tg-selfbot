"""Screenshot service using Playwright (optional dependency)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from selfbot.utils.ssrf import validate_ssrf

logger = logging.getLogger(__name__)

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800
SCREENSHOT_TIMEOUT_MS = 15000

# Prefer system-installed browsers (Edge/Chrome) to avoid downloading Chromium,
# which is geo-blocked on some networks. The empty dict falls back to the
# bundled Playwright Chromium when it has been installed.
_LAUNCH_OPTIONS: tuple[dict[str, object], ...] = (
    {"channel": "msedge"},
    {"channel": "chrome"},
    {},
)

try:  # Playwright is optional.
    from playwright.async_api import async_playwright  # type: ignore[import-not-found]

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ScreenshotError(Exception):
    """Raised when a screenshot cannot be taken."""


class PlaywrightNotInstalledError(ScreenshotError):
    """Raised when Playwright is not installed."""


def _describe(exc: Exception) -> str:
    """Return a useful message for ``exc``, falling back to its class name."""
    detail = str(exc).strip()
    return detail if detail else exc.__class__.__name__


def _browser_hint(exc: Exception) -> str:
    """Return a user-facing message, detecting the common missing-browser case."""
    text = str(exc).lower()
    if not text:
        return "مرورگر راه‌اندازی نشد"
    if "executable doesn't exist" in text or "ms-playwright" in text or "playwright install" in text:
        return (
            "مرورگر کرومیوم نصب نیست. روی سرور اجرا کنید: "
            "`pip install selfbot[screenshot]` و سپس `playwright install chromium`"
        )
    return f"مرورگر راه‌اندازی نشد: {_describe(exc)}"


async def _launch_browser(playwright: Any) -> Any:
    """Launch the first available Chromium, preferring installed Edge/Chrome."""
    last_exc: Exception | None = None
    for options in _LAUNCH_OPTIONS:
        try:
            return await playwright.chromium.launch(**options)
        except Exception as exc:  # noqa: BLE001 - try the next browser channel
            last_exc = exc
            logger.debug("browser channel %s unavailable: %s", options, _describe(exc))
    raise ScreenshotError(_browser_hint(last_exc)) from last_exc


async def capture_screenshot(url: str, output: Path) -> Path:
    """Capture a screenshot of ``url`` and save it to ``output``.

    Raises SSRFBlockedError for internal destinations, and ScreenshotError
    on timeout or browser failure.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise PlaywrightNotInstalledError("playwright not installed")

    validate_ssrf(url)

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        async with async_playwright() as playwright:
            browser = await _launch_browser(playwright)
            try:
                page = await browser.new_page(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
                )
                try:
                    await page.goto(url, timeout=SCREENSHOT_TIMEOUT_MS, wait_until="networkidle")
                except Exception as exc:  # noqa: BLE001 - page errors surface as screenshot failures
                    raise ScreenshotError(f"بارگذاری صفحه انجام نشد: {_describe(exc)}") from exc
                await page.screenshot(path=str(output), full_page=False)
            finally:
                await browser.close()
    except PlaywrightNotInstalledError:
        raise
    except ScreenshotError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("screenshot failed: %s", _describe(exc))
        raise ScreenshotError(_browser_hint(exc)) from exc
    return output
