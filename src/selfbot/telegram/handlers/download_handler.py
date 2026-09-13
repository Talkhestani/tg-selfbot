"""Download command using the yt-dlp service."""

from __future__ import annotations

import asyncio
import logging

from selfbot.messages import persian as msg
from selfbot.services.downloader import DownloadError
from selfbot.telegram.dispatcher import CommandContext, CommandError, CommandSpec

logger = logging.getLogger(__name__)

POLL_INTERVAL = 0.7


def _render_progress(job_id: int, percent: float, status: str) -> str:
    return (
        msg.download_progress_bar(percent, status)
        + f"\n\n📌 شناسه: {job_id}"
    )


async def download_command(ctx: CommandContext) -> None:
    args = ctx.args.strip()
    if not args:
        raise CommandError(msg.DOWNLOAD_NO_URL)

    audio_only = False
    if args.endswith("--audio"):
        audio_only = True
        args = args[: -len("--audio")].strip()

    url = args
    if "://" not in url:
        url = f"https://{url}"

    downloader = ctx.services.downloader
    if not downloader.is_supported_url(url):
        raise CommandError(msg.DOWNLOAD_UNSUPPORTED)

    try:
        job_id = await downloader.submit(
            url, chat_id=ctx.chat_id, reply_to=ctx.event.id, audio_only=audio_only
        )
    except DownloadError as exc:
        raise CommandError(str(exc)) from exc

    # Instead of announcing "در صف قرار گرفت", the command message itself
    # becomes a live progress bar that is edited as the download advances.
    progress = await ctx.respond(_render_progress(job_id, 0.0, "queued"))

    last_text: str | None = None
    while progress is not None:
        state = downloader.status(job_id)
        if state is None:
            return
        status = state["status"]
        if status in {"done", "failed"}:
            break
        text = _render_progress(job_id, state["progress"], status)
        if text != last_text:
            try:
                await progress.edit(text)
            except Exception:  # noqa: BLE001 - keep waiting even if editing fails
                progress = None
            last_text = text
        await asyncio.sleep(POLL_INTERVAL)

    final = await downloader.wait_for(job_id)
    if final is None:
        return

    if final["status"] == "failed":
        text = f"{msg.ERR} {final['error'] or msg.INTERNAL_ERROR}"
        if progress is not None:
            try:
                await progress.edit(text)
                return
            except Exception as exc:  # noqa: BLE001 - fall back to a new reply
                logger.debug("could not edit failed download message: %s", exc)
        await ctx.respond(text)
        return

# The worker sends the file as its own media message; once the file has
    # been delivered the progress bar is no longer needed, so remove it and
    # leave only the downloaded file in the chat.
    if progress is not None:
        try:
            await progress.delete()
        except Exception as exc:  # noqa: BLE001 - the file is already delivered
            logger.debug("could not remove progress message: %s", exc.__class__.__name__)


def register(dispatcher, services) -> None:  # type: ignore[no-untyped-def]
    dispatcher.register(
        CommandSpec(
            name="dl",
            handler=download_command,
            category="message",
            description="دانلود محتوا از سرویس‌های پشتیبانی‌شده (نظیر یوتیوب) و ارسال در تلگرام",
            usage="/dl <url> [--audio]",
            owner_only=True,
            sensitive=True,
        )
    )
