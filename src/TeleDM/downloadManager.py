"""
downloadManager.py — Fully async Download Manager for TeleDM

Features:
- asyncio.Queue for download scheduling
- async worker pool
- async database operations
- async Telegram client download
- correct retry logic
- async-safe speed tracking
- clean callbacks
"""

from __future__ import annotations

import asyncio
import time
import atexit
from pathlib import Path
from typing import Dict, Any

from .database import Database
from .utils import LogManager


class DownloadManager:
    """Async Download Manager for TeleDM."""

    def __init__(self, config: Dict[str, Any], telegram_client):
        self.logger = LogManager.get("DownloadManager")

        # External dependencies
        self.config = config
        self.telegram = telegram_client
        self.db = Database()

        # Config values
        self.max_concurrent = config["max_concurrent_downloads"]
        self.retry_attempts = config["retry_attempts"]
        self.retry_delay = config["retry_delay"]
        self.download_path = Path(config["download_path"]).expanduser()
        self.download_path.mkdir(parents=True, exist_ok=True)

        # Queue + workers
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers: list[asyncio.Task] = []
        self.running = False

        # Tracking info
        self.active: Dict[str, Dict] = {}
        self.speed: Dict[str, float] = {}
        self.start_times: Dict[str, float] = {}
        self.last_update: Dict[str, tuple] = {}

        # Callbacks
        self.progress_callbacks: Dict[str, Any] = {}
        self.status_callbacks: list[Any] = []

        # ensuring graceful exit
        atexit.register(lambda: asyncio.run(self.stop()))

    # -------------------------------------------------------------------------
    # LIFECYCLE METHODS
    # -------------------------------------------------------------------------

    async def start(self):
        if self.running:
            return

        self.running = True
        await self.db.connect()
        self.logger.info("DownloadManager started")

        await self._load_pending_downloads()

        # Start worker tasks
        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(), name=f"worker-{i}")
            self.workers.append(worker)

        self.logger.info(f"Spawned {len(self.workers)} async workers")

    async def stop(self):
        if not self.running:
            return

        self.logger.info("Stopping DownloadManager...")

        self.running = False

        # Cancel workers
        for w in self.workers:
            w.cancel()

        # Await their cancellation
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()

        await self.db.close()
        self.logger.info("DownloadManager stopped")

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    async def add_download(self, file_id, file_name, chat_id=None, message_id=None, metadata=None):
        path = str(self.download_path / file_name)

        # Register in DB
        record_id = await self.db.add_download(
            file_id=file_id,
            file_name=file_name,
            download_path=path,
            chat_id=chat_id,
            message_id=message_id,
            metadata=metadata,
        )

        item = {
            "id": record_id,
            "file_id": file_id,
            "file_name": file_name,
            "download_path": path,
            "chat_id": chat_id,
            "message_id": message_id,
            "retry_count": 0,
        }

        await self.queue.put(item)
        self._notify("download_added", item)

        return record_id

    async def cancel_download(self, file_id):
        item = self.active.get(file_id)

        # Cancel active
        if item:
            item["cancelled"] = True
            await self.db.update_status(file_id, "cancelled")
            self._cleanup(file_id)
            self._notify("download_cancelled", item)
            return

        # Cancel pending
        rec = await self.db.get_download(file_id)
        if rec and rec.status in ("pending", "downloading"):
            await self.db.update_status(file_id, "cancelled")
            self._notify("download_cancelled", rec)

    async def retry_download(self, file_id):
        rec = await self.db.get_download(file_id)
        if not rec or rec.status != "failed":
            return

        await self.db.update_status(file_id, "pending")

        await self.queue.put(
            {
                "id": rec.id,
                "file_id": rec.file_id,
                "file_name": rec.file_name,
                "download_path": rec.download_path,
                "chat_id": rec.chat_id,
                "message_id": rec.message_id,
                "retry_count": rec.retry_count,
            }
        )

        self.logger.info(f"Retry queued: {rec.file_name}")

    async def clear_completed(self):
        return await self.db.delete_completed()

    # -------------------------------------------------------------------------
    # WORKER LOOP
    # -------------------------------------------------------------------------

    async def _worker(self):
        """Async worker that processes downloads."""
        while self.running:
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                await self._process(item)
            except Exception as e:
                self.logger.error(f"Worker error: {e}")
            finally:
                self.queue.task_done()

    # -------------------------------------------------------------------------
    # DOWNLOAD PIPELINE
    # -------------------------------------------------------------------------

    async def _process(self, item):
        file_id = item["file_id"]
        file_name = item["file_name"]
        path = item["download_path"]
        chat_id = item.get("chat_id")
        message_id = item.get("message_id")

        if item.get("cancelled"):
            return

        # Validate that we have chat_id and message_id for Telethon
        if not chat_id or not message_id:
            self.logger.error(f"Missing chat_id or message_id for {file_name}")
            await self.db.update_status(file_id, "failed", "Missing chat_id or message_id")
            self._notify("download_failed", item)
            return

        # Convert chat_id to int if it's a string
        try:
            chat_id = int(chat_id) if isinstance(chat_id, str) else chat_id
            message_id = int(message_id) if isinstance(message_id, str) else message_id
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid chat_id or message_id for {file_name}: {e}")
            await self.db.update_status(file_id, "failed", f"Invalid chat_id or message_id: {e}")
            self._notify("download_failed", item)
            return

        self.active[file_id] = item
        await self.db.update_status(file_id, "downloading")
        self._notify("download_started", item)

        # Get reference to current event loop for progress callback
        loop = asyncio.get_event_loop()

        # progress callback (synchronous wrapper for Telethon)
        def progress(downloaded, total):
            pct = (downloaded / total) * 100 if total else 0

            self._update_speed(file_id, downloaded)
            
            # Schedule DB update in the event loop
            asyncio.run_coroutine_threadsafe(
                self.db.update_progress(file_id, pct, downloaded),
                loop
            )

            cb = self.progress_callbacks.get(file_id)
            if cb:
                # Run callback in a safe way
                try:
                    cb(downloaded, total, pct)
                except Exception:
                    pass

        # download logic
        try:
            success = await self.telegram.download_file(
                chat_id, message_id, path, progress
            )

            if success and not item.get("cancelled"):
                await self.db.update_status(file_id, "completed")
                self._cleanup(file_id)
                self._notify("download_completed", item)
                return

            raise Exception("Cancelled or failed")

        except Exception as exc:
            if item["retry_count"] < self.retry_attempts:
                item["retry_count"] += 1
                await self.db.increment_retry(file_id)

                self.logger.info(f"Retrying {file_name} ({item['retry_count']}/{self.retry_attempts})")
                await asyncio.sleep(self.retry_delay)

                await self.queue.put(item)
            else:
                self.logger.error(f"Failed permanently: {file_name}")
                await self.db.update_status(file_id, "failed", str(exc))
                self._cleanup(file_id)
                self._notify("download_failed", item)

        finally:
            self.active.pop(file_id, None)

    # -------------------------------------------------------------------------
    # UTILS
    # -------------------------------------------------------------------------

    async def _load_pending_downloads(self):
        pending = await self.db.get_pending_downloads()
        for rec in pending:
            await self.queue.put(
                {
                    "id": rec.id,
                    "file_id": rec.file_id,
                    "file_name": rec.file_name,
                    "download_path": rec.download_path,
                    "chat_id": rec.chat_id,
                    "message_id": rec.message_id,
                    "retry_count": rec.retry_count,
                }
            )
        self.logger.info(f"{len(pending)} pending downloads loaded")

    def _update_speed(self, file_id, downloaded):
        now = time.time()

        if file_id not in self.start_times:
            self.start_times[file_id] = now
            self.last_update[file_id] = (now, downloaded)
            self.speed[file_id] = 0
            return

        last_time, last_bytes = self.last_update[file_id]
        diff = now - last_time

        if diff >= 0.5:
            rate = (downloaded - last_bytes) / diff
            prev = self.speed.get(file_id, 0)
            self.speed[file_id] = prev * 0.7 + rate * 0.3
            self.last_update[file_id] = (now, downloaded)

    def _cleanup(self, file_id):
        self.start_times.pop(file_id, None)
        self.last_update.pop(file_id, None)
        self.speed.pop(file_id, None)

    def _notify(self, event, item):
        for cb in self.status_callbacks:
            try:
                cb(event, item)
            except Exception:
                pass
