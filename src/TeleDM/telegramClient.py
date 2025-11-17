"""
telegramClient.py — Telethon-based async Telegram client for TeleDM
Handles:
- one-time user authentication (phone login)
- session reuse
- async file downloads with progress callbacks
- getting message & file info
"""

from __future__ import annotations

import atexit
import asyncio

from pathlib import Path
from typing import Optional, Callable, Any

from telethon import TelegramClient as _TelethonClient, errors
from telethon.tl.types import Message

from .utils import LogManager, get_session_dir
from .utils import ConfigManager


class TelegramClient:
    """Async Telethon wrapper providing a clean API for the DownloadManager."""

    def __init__(self, api_id: int, api_hash: str, phone: str):
        # API credentials
        if not api_id or not api_hash or not phone:
            config_mgr = ConfigManager()
            stored_cfg = config_mgr.get_telegram_config()
            self.api_id = api_id or stored_cfg.api_id
            self.api_hash = api_hash or stored_cfg.api_hash
            self.phone = phone or stored_cfg.phone
        else:
            self.api_id = api_id
            self.api_hash = api_hash
            self.phone = phone

        self.logger = LogManager.get("TelegramClient")

        # Telethon session file stored inside app's session directory
        session_dir = Path(get_session_dir())
        session_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = str(session_dir / "telethon")

        self.client: Optional[_TelethonClient] = None
        self.initialized = False

        # ensuring graceful exit
        atexit.register(lambda: asyncio.run(self.close()))

    # ----------------------------------------------------------------------
    # Initialization & Login
    # ----------------------------------------------------------------------

    async def initialize(self) -> bool:
        """
        Initialize Telethon client.
        If session exists → auto-login.
        If not → ask user for code (only on first run).
        """
        try:
            self.client = _TelethonClient(
                session=self.session_path,
                api_id=self.api_id,
                api_hash=self.api_hash,
            )

            await self.client.connect()

            if not await self.client.is_user_authorized():
                self.logger.info("No valid session found. Sending login code...")
                await self.client.send_code_request(self.phone)

                code = input("Enter the code you received on Telegram: ")
                await self.client.sign_in(self.phone, code)

                self.logger.info("Login successful. Session saved.")

            else:
                self.logger.info("Telethon session loaded. Logged in automatically.")

            self.initialized = True
            return True

        except errors.PhoneCodeInvalidError:
            self.logger.error("Invalid authentication code.")
            return False

        except Exception as e:
            self.logger.error(f"Error initializing Telegram client: {e}")    # TODO: handle corrupted/invalid session files
            return False

    # ----------------------------------------------------------------------
    # Download file
    # ----------------------------------------------------------------------

    async def download_file(
        self,
        chat_id: int,
        message_id: int,
        download_path: str,
        progress_cb: Optional[Callable[[int, int], Any]] = None,
    ) -> bool:
        """
        Download a file from Telegram using chat_id + message_id.
        """

        if not self.initialized:
            raise RuntimeError("TelegramClient not initialized")

        try:
            msg: Message = await self.client.get_messages(entity=chat_id, ids=message_id)

            if not msg or not msg.media:
                self.logger.error(f"Message {chat_id}:{message_id} has no downloadable media.")
                return False

            dst = Path(download_path)
            dst.parent.mkdir(parents=True, exist_ok=True)

            # Progress wrapper for Telethon
            def telethon_progress(current, total):
                try:
                    if progress_cb:
                        progress_cb(current, total)
                except Exception:
                    pass

            await self.client.download_media(
                msg,
                file=str(dst),
                progress_callback=telethon_progress,
            )

            self.logger.info(f"Downloaded → {dst}")
            return True

        except Exception as e:
            self.logger.error(f"Download failed for {chat_id}:{message_id} — {e}")
            raise

    # ----------------------------------------------------------------------
    # File Info
    # ----------------------------------------------------------------------

    async def get_file_info(self, chat_id, message_id) -> Optional[dict]:
        if not self.initialized:
            raise RuntimeError("TelegramClient not initialized")

        try:
            msg = await self.client.get_messages(entity=chat_id, ids=message_id)
            if not msg or not msg.media:
                return None

            return {
                "chat_id": chat_id,
                "message_id": message_id,
                "file_size": msg.file.size if msg.file else None,
                "file_name": msg.file.name if msg.file else None,
                "mime_type": msg.file.mime_type if msg.file else None,
            }

        except Exception as e:
            self.logger.error(f"Error getting file info: {e}")
            return None

    # ----------------------------------------------------------------------
    # Cleanup
    # ----------------------------------------------------------------------

    async def close(self):
        try:
            if self.client:
                await self.client.disconnect()
            self.logger.info("Telethon client closed.")
        except Exception as e:
            self.logger.error(f"Error closing client: {e}")
