"""Screenshot service using Playwright (optional dependency)."""

from __future__ import annotations

import logging
from pathlib import Path

from selfbot.utils.ssrf import validate_ssrf

logger = logging.getLogger(__name__)

VIEWPORT_WIDTH = 1280
VIEWPORT_HEIGHT = 800
SCREENSHOT_TIMEOUT_MS = 15000

try:  # Playwright is optional.
    from playwright.async_api import async_playwright  # type: ignore[import-not-found]

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ScreenshotError(Exception):
    """Raised when a screenshot cannot be taken."""


class PlaywrightNotInstalledError(ScreenshotError):
    """Raised when Playwright is not installed."""


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
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page(
                    viewport={"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT}
                )
                try:
                    await page.goto(url, timeout=SCREENSHOT_TIMEOUT_MS, wait_until="networkidle")
                except Exception as exc:  # noqa: BLE001 - page errors surface as screenshot failures
                    raise ScreenshotError(f"بارگذاری صفحه انجام نشد: {exc.__class__.__name__}") from exc
                await page.screenshot(path=str(output), full_page=False)
            finally:
                await browser.close()
    except PlaywrightNotInstalledError:
        raise
    except ScreenshotError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("screenshot failed: %s", exc.__class__.__name__)
        raise ScreenshotError("مرورگر راه‌اندازی نشد") from exc
    return output
