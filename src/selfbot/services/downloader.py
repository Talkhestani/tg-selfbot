"""yt-dlp based download service with a queue and Telegram upload."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp
from telethon import TelegramClient

from selfbot.config import Settings
from selfbot.messages import persian as msg
from selfbot.utils.validators import is_valid_url

logger = logging.getLogger(__name__)

SUPPORTED_PATTERNS = (
    "youtu.be",
    "youtube.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "soundcloud.com",
    "vimeo.com",
    "facebook.com",
    "twitch.tv",
    "spotify.com",
    "bilibili.com",
)

MAX_QUEUE_SIZE = 5


class DownloadError(Exception):
    """Raised when a download cannot be processed."""


class DownloadService:
    """Queues and executes downloads, then uploads the file to Telegram."""

    def __init__(self, client: TelegramClient, settings: Settings) -> None:
        self.client = client
        self.settings = settings
        self._queue: asyncio.Queue[int] = asyncio.Queue(maxsize=MAX_QUEUE_SIZE)
        self._jobs: dict[int, dict[str, Any]] = {}
        self._next_id = 1
        self._worker: asyncio.Task[Any] | None = None
        self._lock = asyncio.Lock()

    # -- lifecycle --------------------------------------------------------
    def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._worker = asyncio.create_task(self._run_worker(), name="download-worker")

    def shutdown(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    # -- public API -------------------------------------------------------
    def is_supported_url(self, url: str) -> bool:
        if not is_valid_url(url):
            return False
        lowered = url.lower()
        return any(pattern in lowered for pattern in SUPPORTED_PATTERNS)

    async def submit(
        self, url: str, *, chat_id: int, reply_to: int | None = None, audio_only: bool = False
    ) -> int:
        """Queue a download and return its job id."""
        if not self.is_supported_url(url):
            raise DownloadError(msg.DOWNLOAD_UNSUPPORTED)
        async with self._lock:
            if len(self._jobs) >= MAX_QUEUE_SIZE:
                raise DownloadError(msg.DOWNLOAD_TOO_MANY)
            job_id = self._next_id
            self._next_id += 1
            self._jobs[job_id] = {
                "id": job_id,
                "url": url,
                "chat_id": chat_id,
                "reply_to": reply_to,
                "audio_only": audio_only,
                "status": "queued",
                "progress": 0.0,
                "error": None,
                "done": asyncio.Event(),
                "file_path": None,
            }
            await self._queue.put(job_id)
        return job_id

    def status(self, job_id: int) -> dict[str, Any] | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        return {
            "id": job["id"],
            "status": job["status"],
            "progress": job["progress"],
            "error": job["error"],
        }

    def is_busy(self) -> bool:
        return any(job["status"] in {"downloading", "uploading"} for job in self._jobs.values())

    async def wait_for(self, job_id: int) -> dict[str, Any] | None:
        """Await the completion of a download job and return its final status."""
        job = self._jobs.get(job_id)
        if job is None:
            return None
        await job["done"].wait()
        return self.status(job_id)

    # -- worker -----------------------------------------------------------
    async def _run_worker(self) -> None:
        while True:
            job_id = await self._queue.get()
            job = self._jobs.get(job_id)
            if job is None:
                self._queue.task_done()
                continue
            try:
                await self._process(job)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 - report and continue
                logger.error("download job %s crashed: %s", job_id, exc)
                job["status"] = "failed"
                job["error"] = msg.INTERNAL_ERROR
            finally:
                job["done"].set()
                self._queue.task_done()

    async def _process(self, job: dict[str, Any]) -> None:
        url = job["url"]
        job["status"] = "downloading"
        work_dir = self.settings.download_path / f"job_{job['id']}"
        work_dir.mkdir(parents=True, exist_ok=True)

        options: dict[str, Any] = {
            "outtmpl": str(work_dir / "%(title).120s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "max_filesize": self.settings.max_download_size_mb * 1024 * 1024,
            "socket_timeout": self.settings.download_timeout,
            "progress_hooks": [self._make_progress_hook(job)],
            "restrictfilenames": False,
        }
        if job["audio_only"]:
            options.update(
                {
                    "format": "bestaudio/best",
                    "extractaudio": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            )
        else:
            options["format"] = "best[ext=mp4]/best"

        try:
            file_path = await asyncio.get_running_loop().run_in_executor(
                None, self._download_sync, url, options
            )
        except asyncio.CancelledError:
            raise
        except yt_dlp.utils.DownloadError as exc:
            job["status"] = "failed"
            job["error"] = self._friendly_download_error(str(exc))
            logger.info("download failed for %s: %s", url, exc)
            shutil.rmtree(work_dir, ignore_errors=True)
            return
        except Exception as exc:  # noqa: BLE001
            job["status"] = "failed"
            job["error"] = msg.DOWNLOAD_FAILED.format(msg.INTERNAL_ERROR)
            logger.warning("download error for %s: %s", url, exc.__class__.__name__)
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        if file_path is None:
            job["status"] = "failed"
            job["error"] = msg.DOWNLOAD_FAILED.format("فایل ساخته نشد")
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        job["file_path"] = file_path
        await self._upload(job, work_dir)

    def _download_sync(self, url: str, options: dict[str, Any]) -> str | None:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            requested = info.get("requested_downloads") or []
            if requested:
                path = requested[0].get("filepath")
                if path and Path(path).exists():
                    return str(path)
                # An audio conversion may have produced a different file.
                base = Path(requested[0].get("filepath", ""))
            else:
                base = Path(ydl.prepare_filename(info))
            if base.exists():
                return str(base)
            candidates = sorted(base.parent.glob("*"))
            if candidates:
                largest = max(candidates, key=lambda p: p.stat().st_size)
                return str(largest)
            return None

    def _make_progress_hook(self, job: dict[str, Any]) -> Callable[[dict[str, Any]], None]:
        def hook(data: dict[str, Any]) -> None:
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                if total:
                    job["progress"] = round(downloaded / total * 100, 1)
            elif data.get("status") == "finished":
                job["progress"] = 100.0

        return hook

    async def _upload(self, job: dict[str, Any], work_dir: Path) -> None:
        file_path: str | None = job.get("file_path")
        if not file_path or not Path(file_path).exists():  # noqa: ASYNC240 - quick local check
            job["status"] = "failed"
            job["error"] = msg.DOWNLOAD_FAILED.format("فایل پیدا نشد")
            shutil.rmtree(work_dir, ignore_errors=True)
            return

        job["status"] = "uploading"
        try:
            max_size = self.settings.max_download_size_mb * 1024 * 1024
            file_size = await asyncio.to_thread(Path(file_path).stat)  # noqa: ASYNC240 - getsize via thread
            if file_size.st_size > max_size:
                raise DownloadError(msg.DOWNLOAD_SIZE_EXCEEDED)
            chat_id = job["chat_id"]
            caption = f"{msg.DOWNLOAD_DONE}\n📎 {Path(file_path).name}"
            await self.client.send_file(
                chat_id, file_path, caption=caption, reply_to=job["reply_to"]
            )
            job["status"] = "done"
        except Exception as exc:  # noqa: BLE001
            job["status"] = "failed"
            job["error"] = msg.DOWNLOAD_FAILED.format(self._friendly_upload_error(exc))
            logger.warning("upload failed for job %s: %s", job["id"], exc.__class__.__name__)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    # -- error translation ------------------------------------------------
    @staticmethod
    def _friendly_download_error(text: str) -> str:
        lowered = text.lower()
        if "unsupported url" in lowered or "is not a valid url" in lowered:
            return msg.DOWNLOAD_UNSUPPORTED
        if "file is larger" in lowered or "max_filesize" in lowered:
            return msg.DOWNLOAD_SIZE_EXCEEDED
        if "requested format is not available" in lowered:
            return "کیفیت درخواستی در دسترس نیست."
        if "private" in lowered or "login required" in lowered or "sign in" in lowered:
            return "این محتوا نیاز به دسترسی یا ورود به حساب دارد."
        return msg.DOWNLOAD_FAILED.format("لینک در دسترس نیست یا پشتیبانی نمی‌شود")

    @staticmethod
    def _friendly_upload_error(exc: Exception) -> str:
        from telethon.errors import FilePartMissingError

        if isinstance(exc, FilePartMissingError):
            return "ارسال فایل ناقص ماند."
        return msg.INTERNAL_ERROR
