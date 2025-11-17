"""
utils.py — Utility functions and classes for TeleDM (logging, paths, config).

Features
- platformdirs-based application directories (data, logs, sessions)
- robust RotatingFileHandler-based logging (prevents duplicate handlers)
- ConfigManager that creates sensible defaults on first run
- Typed small dataclasses for configs returned by ConfigManager
- Safe for use in async contexts (uses standard logging; no blocking calls in async loops)
"""

from __future__ import annotations

import logging
import logging.handlers
import queue
import atexit
import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import configparser
from typing import Optional, Any

import platformdirs

# --------------------------
# Constants / Defaults
# --------------------------
APP_NAME = "TeleDM"
APP_AUTHOR = "ADPer"
CONFIG_FILE_NAME = "teledmcfg.ini"
LOG_FILE_NAME = "teledmlog.log"
SESSION_DIR_NAME = "sessions"
DOWNLOAD_DIR_NAME = "downloads"
DATABASE_FILE_NAME = "teledmdb.db"

DEFAULT_MAX_LOG_BYTES = 5 * 1024 * 1024  # 5 MB
DEFAULT_LOG_BACKUP_COUNT = 5

# --------------------------
# Dataclasses for typed configs
# --------------------------
@dataclass
class TelegramConfig:
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class DownloadConfig:
    download_path: str
    max_concurrent_downloads: int = 3
    chunk_size: int = 1 * 1024 * 1024  # 1 MiB
    retry_attempts: int = 5
    retry_delay: int = 5  # seconds


# --------------------------
# Paths & helpers
# --------------------------
def get_app_dir() -> str:
    """Return and ensure application data directory exists."""
    app_dir = platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    Path(app_dir).mkdir(parents=True, exist_ok=True)
    return app_dir


def get_config_path() -> str:
    """Return full path to config file (create empty file if missing)."""
    cfg = Path(get_app_dir()) / CONFIG_FILE_NAME
    cfg.parent.mkdir(parents=True, exist_ok=True)
    if not cfg.exists():
        # create empty file so editors/CLI can open it; we don't populate defaults here
        cfg.touch()
    return str(cfg)


def get_log_path() -> str:
    """Return full path to log file (creates parent dir)."""
    lp = Path(get_app_dir()) / LOG_FILE_NAME
    lp.parent.mkdir(parents=True, exist_ok=True)
    # do not touch file to avoid timestamp changes; handler will create it
    return str(lp)


def get_session_dir() -> str:
    d = Path(get_app_dir()) / SESSION_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def get_default_download_dir() -> str:
    """Return user's system Downloads directory."""
    d = Path(platformdirs.user_downloads_dir())
    d.mkdir(parents=True, exist_ok=True)
    return str(d)


def now_str(fmt: str = "%Y-%m-%d_%H-%M-%S") -> str:
    return datetime.now().strftime(fmt)


def get_database_path() -> str:
    """Return full path to database file (creates parent dir)."""
    dbp = Path(get_app_dir()) / DATABASE_FILE_NAME
    dbp.parent.mkdir(parents=True, exist_ok=True)
    return str(dbp)


# --------------------------
# Logging
# --------------------------
class LogManager:
    """
    Centralized async-safe logging setup using QueueHandler and QueueListener.
    
    This implementation ensures that logging operations don't block async event loops
    by offloading all I/O operations to a separate thread via a queue.

    Usage:
        LogManager.setup()            # sets up root logger for APP_NAME (idempotent)
        logger = LogManager.get("module.name")
        
    Cleanup:
        LogManager.shutdown()         # stops the queue listener (automatic on exit)
    """

    _is_setup = False
    _queue_listener: Optional[logging.handlers.QueueListener] = None
    _log_queue: Optional[queue.Queue] = None

    @classmethod
    def setup(
        cls,
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        max_bytes: int = DEFAULT_MAX_LOG_BYTES,
        backup_count: int = DEFAULT_LOG_BACKUP_COUNT,
    ) -> None:
        """Configure async-safe logging for the application. Idempotent."""
        if cls._is_setup:
            return

        log_file = log_file or get_log_path()
        logger = logging.getLogger(APP_NAME)
        logger.setLevel(level)

        # Prevent adding handlers multiple times (idempotent)
        if logger.handlers:
            cls._is_setup = True
            return

        # Create thread-safe queue for async-safe logging
        cls._log_queue = queue.Queue(-1)  # unlimited size
        
        # Create actual handlers that will process logs in a separate thread
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)
        file_handler.setLevel(level)

        console_handler = logging.StreamHandler()
        console_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S")
        console_handler.setFormatter(console_fmt)
        console_handler.setLevel(level)

        # QueueListener processes logs from queue in a separate thread
        # This prevents blocking the async event loop
        cls._queue_listener = logging.handlers.QueueListener(
            cls._log_queue,
            file_handler,
            console_handler,
            respect_handler_level=True
        )
        cls._queue_listener.start()

        # Add QueueHandler to logger (non-blocking, async-safe)
        queue_handler = logging.handlers.QueueHandler(cls._log_queue)
        logger.addHandler(queue_handler)

        logger.info("Async-safe LogManager initialized. Logging to %s", log_file)
        cls._is_setup = True
        
        # Register cleanup on exit
        atexit.register(lambda: cls.shutdown())

    @classmethod
    def shutdown(cls) -> None:
        """Stop the queue listener and flush remaining logs. Safe to call multiple times."""
        logger = logging.getLogger(APP_NAME)
        logger.info("Stopping the Log Manager...")

        if cls._queue_listener is not None:
            cls._queue_listener.stop()
            cls._queue_listener = None
        cls._log_queue = None
        cls._is_setup = False

    @staticmethod
    def get(name: str) -> logging.Logger:
        """Get a logger under the application namespace (APP_NAME.name)."""
        return logging.getLogger(f"{APP_NAME}.{name}")

    # ----- end of LogManager -----
    def __del__(self):
        """Ensure shutdown on deletion."""
        try:
            LogManager.shutdown()
        except Exception:
            pass

# --------------------------
# Config Management
# --------------------------
class ConfigManager:
    """Loads, validates and provides application configuration."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        # Ensure logging is initialized so we can log during config bootstrapping
        LogManager.setup()
        self._logger = LogManager.get("ConfigManager")

        self.config_path = config_path or get_config_path()
        self._cfg = configparser.ConfigParser()
        self._ensure_config_exists()
        self.load()
        
        # Register cleanup on exit (like LogManager does)
        atexit.register(lambda: self.save())

    def _ensure_config_exists(self) -> None:
        """If file is missing or empty, write default sections (no secrets)."""
        p = Path(self.config_path)
        if not p.exists() or p.stat().st_size == 0:
            self._logger.info("Config file %s missing or empty — creating default template.", self.config_path)
            # Create a default template with empty values where appropriate
            template = configparser.ConfigParser()
            template["telegram"] = {
                    "api_id": None,
                    "api_hash": None,
                    "phone": None
            }
            template["downloads"] = {
                "download_path": get_default_download_dir(),
                "max_concurrent_downloads": "3",
                "chunk_size": str(1 * 1024 * 1024),
                "retry_attempts": "5",
                "retry_delay": "5",
            }
            with open(self.config_path, "w", encoding="utf-8") as fh:
                template.write(fh)
            self._logger.info("Wrote config template to %s", self.config_path)

    def load(self) -> None:
        """Read the config file into memory."""
        try:
            read = self._cfg.read(self.config_path, encoding="utf-8")
            if not read:
                self._logger.warning("Config file %s could not be read or is empty", self.config_path)
            else:
                self._logger.info("Config loaded from %s", self.config_path)
        except Exception as exc:
            self._logger.exception("Failed to read config file %s: %s", self.config_path, exc)
            raise

    def save(self) -> None:
        """Persist current in-memory config to disk."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as fh:
                self._cfg.write(fh)
            self._logger.info("Configuration saved to %s", self.config_path)
        except Exception:
            self._logger.exception("Failed to save config to %s", self.config_path)
            pass # Don't raise during cleanup

    # ----- getters (typed) -----
    def get_telegram_config(self) -> TelegramConfig:
        """Return TelegramConfig with api_id, api_hash, and phone from config file."""
        try:
            sec = "telegram"
            if self._cfg.has_section(sec) and any(self._cfg.options(sec)):
                api_id = self._cfg.get(sec, "api_id", fallback=None)
                api_hash = self._cfg.get(sec, "api_hash", fallback=None)
                phone = self._cfg.get(sec, "phone", fallback=None)

                if api_id and api_hash and phone:
                    return TelegramConfig(api_id=int(api_id), api_hash=api_hash, phone=phone)
            
            # Return empty config if not configured
            return TelegramConfig()
        except Exception as e:
            self._logger.error("Error reading telegram config: %s", e)
            return TelegramConfig()

    def get_download_config(self) -> DownloadConfig:
        sec = "downloads"
        try:
            download_path = self._cfg.get(sec, "download_path", fallback=get_default_download_dir())
            max_concurrent_downloads = int(self._cfg.get(sec, "max_concurrent_downloads", fallback="3"))
            chunk_size = int(self._cfg.get(sec, "chunk_size", fallback=str(1 * 1024 * 1024)))
            retry_attempts = int(self._cfg.get(sec, "retry_attempts", fallback="5"))
            retry_delay = int(self._cfg.get(sec, "retry_delay", fallback="5"))

            return DownloadConfig(
                download_path=str(Path(download_path).expanduser()),
                max_concurrent_downloads=max_concurrent_downloads,
                chunk_size=chunk_size,
                retry_attempts=retry_attempts,
                retry_delay=retry_delay,
            )
        except Exception:
            self._logger.exception("Error reading download configuration; using defaults.")
            return DownloadConfig(download_path=get_default_download_dir())


    # ----- raw access for advanced users -----
    def get_raw(self) -> configparser.ConfigParser:
        """Return the underlying ConfigParser instance for advanced reads/writes."""
        return self._cfg

    def set_option(self, section: str, option: str, value: Any) -> None:
        """Convenience to set and persist an option."""
        if not self._cfg.has_section(section):
            self._cfg.add_section(section)
        self._cfg.set(section, option, str(value))
        self.save()

# --------------------------
# Example quick usage
# --------------------------
if __name__ == "__main__":
    # Quick smoke test
    LogManager.setup()  # idempotent
    logger = LogManager.get("main")
    logger.info("Starting TeleDM utilities smoke test")

    cfgm = ConfigManager()  # ensures config exists and loads it
    tconf = cfgm.get_telegram_config()
    dconf = cfgm.get_download_config()

    logger.info("Telegram config: %s", tconf)
    logger.info("Download config: %s", dconf)
