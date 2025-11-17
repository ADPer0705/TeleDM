"""
database.py — Async-safe SQLite database layer for TeleDM.

Implements:
- a single long-lived SQLite connection
- WAL mode for concurrency
- asyncio.Lock for safe usage across coroutines
- aiosqlite for non-blocking database I/O
- automatic schema creation & indexing
- JSON encoding/decoding for metadata
"""

from __future__ import annotations

import json
import asyncio
import aiosqlite
import atexit
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from .utils import LogManager, get_database_path


# ---------------------------------------------------------------------------
# Dataclasses for typed row mapping
# ---------------------------------------------------------------------------

@dataclass
class DownloadRecord:
    id: int
    file_id: str
    file_name: str
    file_size: Optional[int]
    download_path: Optional[str]
    status: str
    progress: float
    downloaded_bytes: int
    error_message: Optional[str]
    retry_count: int
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    chat_id: Optional[str]
    message_id: Optional[int]
    metadata: Optional[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Database Manager
# ---------------------------------------------------------------------------

class Database:
    """Async-safe SQLite database for storing download information."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_database_path()
        self.logger = LogManager.get("Database")
        self._lock = asyncio.Lock()
        self._conn: Optional[aiosqlite.Connection] = None

        atexit.register(lambda: asyncio.run(self.close()))

    # ---------------------- LIFECYCLE ----------------------

    async def connect(self):
        """Open SQLite connection with async support and apply PRAGMAs."""
        if self._conn is not None:
            return

        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row

        # Apply optimal pragmas
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")

        await self._create_schema()
        await self._create_indexes()

        self.logger.info("Async SQLite connection established.")

    async def close(self):
        """Gracefully close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            self.logger.info("Database connection closed.")

    # ---------------------- SCHEMA ----------------------

    async def _create_schema(self):
        """Create tables if not exists."""
        async with self._conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                download_path TEXT,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                downloaded_bytes INTEGER DEFAULT 0,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                chat_id TEXT,
                message_id INTEGER,
                metadata TEXT
            )
        """):
            pass

        async with self._conn.execute("""
            CREATE TABLE IF NOT EXISTS download_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP
            )
        """):
            pass

        await self._conn.commit()
        self.logger.info("Database schema created.")

    async def _create_indexes(self):
        """Create indexes for performance."""
        queries = [
            "CREATE INDEX IF NOT EXISTS idx_file_id ON downloads(file_id);",
            "CREATE INDEX IF NOT EXISTS idx_status ON downloads(status);",
            "CREATE INDEX IF NOT EXISTS idx_created_at ON downloads(created_at);",
        ]

        for q in queries:
            await self._conn.execute(q)

        await self._conn.commit()
        self.logger.info("Database indexes ensured.")

    # --------------------------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------------------------

    def _row_to_record(self, row: aiosqlite.Row) -> DownloadRecord:
        md = row["metadata"]
        return DownloadRecord(
            id=row["id"],
            file_id=row["file_id"],
            file_name=row["file_name"],
            file_size=row["file_size"],
            download_path=row["download_path"],
            status=row["status"],
            progress=row["progress"],
            downloaded_bytes=row["downloaded_bytes"],
            error_message=row["error_message"],
            retry_count=row["retry_count"],
            created_at=row["created_at"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            chat_id=row["chat_id"],
            message_id=row["message_id"],
            metadata=json.loads(md) if md else None,
        )

    # --------------------------------------------------------------------------
    # CRUD METHODS
    # --------------------------------------------------------------------------

    async def add_download(self, *, file_id: str, file_name: str,
                           file_size: Optional[int] = None,
                           download_path: Optional[str] = None,
                           chat_id: Optional[str] = None,
                           message_id: Optional[int] = None,
                           metadata: Optional[Dict] = None) -> int:
        """Insert a new download item."""
        async with self._lock:
            q = """
                INSERT OR IGNORE INTO downloads
                (file_id, file_name, file_size, download_path, chat_id, message_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            md = json.dumps(metadata) if metadata else None
            await self._conn.execute(q, (file_id, file_name, file_size,
                                         download_path, chat_id, message_id, md))
            await self._conn.commit()

            # Fetch row id
            async with self._conn.execute(
                "SELECT id FROM downloads WHERE file_id = ?", (file_id,)
            ) as cursor:
                row = await cursor.fetchone()
                self.logger.info(f"Added/exists: {file_name} → DB ID {row['id']}")
                return row["id"]

    async def update_progress(self, file_id: str, *, progress: float, downloaded_bytes: int):
        """Update progress for a download."""
        async with self._lock:
            await self._conn.execute("""
                UPDATE downloads
                SET progress = ?, downloaded_bytes = ?
                WHERE file_id = ?
            """, (progress, downloaded_bytes, file_id))
            await self._conn.commit()

    async def update_status(self, file_id: str, status: str,
                            error_message: Optional[str] = None):
        """Update status and timestamps."""
        async with self._lock:
            ts = None
            if status == "downloading":
                ts = "started_at"
            elif status in ("completed", "failed"):
                ts = "completed_at"

            if ts:
                await self._conn.execute(
                    f"""
                    UPDATE downloads
                    SET status = ?, error_message = ?, {ts} = CURRENT_TIMESTAMP
                    WHERE file_id = ?
                    """,
                    (status, error_message, file_id),
                )
            else:
                await self._conn.execute("""
                    UPDATE downloads
                    SET status = ?, error_message = ?
                    WHERE file_id = ?
                """, (status, error_message, file_id))

            await self._conn.commit()

            self.logger.info(f"{file_id} status → {status}")

    async def increment_retry(self, file_id: str):
        async with self._lock:
            await self._conn.execute("""
                UPDATE downloads
                SET retry_count = retry_count + 1
                WHERE file_id = ?
            """, (file_id,))
            await self._conn.commit()

    # --------------------------------------------------------------------------
    # READ METHODS
    # --------------------------------------------------------------------------

    async def get_download(self, file_id: str) -> Optional[DownloadRecord]:
        async with self._lock:
            async with self._conn.execute(
                "SELECT * FROM downloads WHERE file_id = ?", (file_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return self._row_to_record(row) if row else None

    async def get_pending_downloads(self) -> List[DownloadRecord]:
        async with self._lock:
            async with self._conn.execute("""
                SELECT * FROM downloads
                WHERE status IN ('pending', 'paused', 'failed')
                ORDER BY created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_record(r) for r in rows]

    async def get_all_downloads(self) -> List[DownloadRecord]:
        async with self._lock:
            async with self._conn.execute("""
                SELECT * FROM downloads
                ORDER BY created_at DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_record(r) for r in rows]

    # --------------------------------------------------------------------------
    # DELETE
    # --------------------------------------------------------------------------

    async def delete_download(self, file_id: str):
        async with self._lock:
            await self._conn.execute("DELETE FROM downloads WHERE file_id = ?", (file_id,))
            await self._conn.commit()
            self.logger.info(f"Deleted {file_id} from database.")

    async def delete_completed(self) -> int:
        async with self._lock:
            cursor = await self._conn.execute("""
                DELETE FROM downloads
                WHERE status IN ('completed', 'cancelled')
            """)
            await self._conn.commit()
            cnt = cursor.rowcount
            self.logger.info(f"Deleted {cnt} completed/cancelled rows.")
            return cnt
