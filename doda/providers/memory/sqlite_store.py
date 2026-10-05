"""``SQLiteMemoryStore`` — MemoryStore portining stdlib ``sqlite3`` implementatsiyasi.

Tashqi kutubxonasiz (SQLModel/SQLAlchemy shart emas — port allaqachon DB'ni abstraktlaydi;
Postgres kerak bo'lsa yangi provider yoziladi). ``sqlite3`` sinxron, shuning uchun barcha
amal ``asyncio.to_thread`` orqali ishga tushiriladi (Async-First) va bitta ulanish + ``Lock``
bilan ketma-ketlashtiriladi. Semantik qidiruv: berilgan vektor bilan saqlangan vektorlar
o'rtasida kosinus-o'xshashlik (minglab yozuv uchun yetarli; keyin Vector DB port ortida).
"""

from __future__ import annotations

import asyncio
import math
import sqlite3
import threading
from array import array
from collections.abc import Sequence
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from doda.core.models.memory import MemoryItem, MemoryType

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id         TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL,
    type       TEXT NOT NULL,
    content    TEXT NOT NULL,
    importance REAL NOT NULL,
    source     TEXT NOT NULL,
    created_at TEXT NOT NULL,
    valid      INTEGER NOT NULL,
    embedding  BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_memories_filter ON memories (user_id, type, valid);
CREATE INDEX IF NOT EXISTS ix_memories_created ON memories (created_at);
"""

_COLUMNS = "id, user_id, type, content, importance, source, created_at, valid, embedding"


def _to_blob(vector: Sequence[float]) -> bytes:
    return array("f", vector).tobytes()


def _from_blob(blob: bytes) -> list[float]:
    buffer = array("f")
    buffer.frombytes(blob)
    return list(buffer)


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b, strict=False):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


def _row_to_item(row: Any) -> MemoryItem:
    return MemoryItem(
        id=str(row[0]),
        user_id=str(row[1]),
        type=MemoryType(str(row[2])),
        content=str(row[3]),
        importance=float(row[4]),
        source=str(row[5]),
        created_at=datetime.fromisoformat(str(row[6])),
        valid=bool(row[7]),
    )


class SQLiteMemoryStore:
    """SQLite asosidagi xotira saqlagich (ulanish lazy quriladi)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    # ---- ulanish (lazy; lock chaqiruvchida ushlanadi) ----
    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self._path, check_same_thread=False)
            conn.executescript(_SCHEMA)
            conn.commit()
            self._conn = conn
        return self._conn

    def close(self) -> None:
        """Ulanishni yopadi (resurs sizishining oldini oladi)."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __del__(self) -> None:
        # GC paytida ulanish yopiladi (ResourceWarning bo'lmasin). Xato bo'lsa jim.
        conn = getattr(self, "_conn", None)
        if conn is not None:
            with suppress(Exception):
                conn.close()

    # ---- async port metodlari ----
    async def add(self, item: MemoryItem, embedding: Sequence[float]) -> None:
        await asyncio.to_thread(self._add_sync, item, list(embedding))

    async def search(
        self,
        embedding: Sequence[float],
        k: int = 5,
        *,
        user_id: str | None = None,
        types: Sequence[MemoryType] | None = None,
    ) -> list[MemoryItem]:
        return await asyncio.to_thread(self._search_sync, list(embedding), k, user_id, types)

    async def recent(
        self,
        n: int = 20,
        *,
        user_id: str | None = None,
        types: Sequence[MemoryType] | None = None,
    ) -> list[MemoryItem]:
        return await asyncio.to_thread(self._recent_sync, n, user_id, types)

    async def get(self, memory_id: str) -> MemoryItem | None:
        return await asyncio.to_thread(self._get_sync, memory_id)

    async def delete(self, memory_id: str) -> None:
        await asyncio.to_thread(self._delete_sync, memory_id)

    async def purge_older_than(self, cutoff: str, *, keep_types: Sequence[MemoryType] = ()) -> int:
        return await asyncio.to_thread(self._purge_sync, cutoff, keep_types)

    # ---- sinxron amallar (thread ichida, lock bilan) ----
    def _add_sync(self, item: MemoryItem, embedding: list[float]) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                f"INSERT OR REPLACE INTO memories ({_COLUMNS}) VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    item.id,
                    item.user_id,
                    item.type.value,
                    item.content,
                    item.importance,
                    item.source,
                    item.created_at.isoformat(),
                    1 if item.valid else 0,
                    _to_blob(embedding),
                ),
            )
            conn.commit()

    def _filter_clause(
        self, user_id: str | None, types: Sequence[MemoryType] | None
    ) -> tuple[str, list[Any]]:
        clauses = ["valid = 1"]
        params: list[Any] = []
        if user_id is not None:
            clauses.append("user_id = ?")
            params.append(user_id)
        if types:
            placeholders = ",".join("?" for _ in types)
            clauses.append(f"type IN ({placeholders})")
            params.extend(t.value for t in types)
        return " WHERE " + " AND ".join(clauses), params

    def _search_sync(
        self,
        embedding: list[float],
        k: int,
        user_id: str | None,
        types: Sequence[MemoryType] | None,
    ) -> list[MemoryItem]:
        where, params = self._filter_clause(user_id, types)
        with self._lock:
            rows = (
                self._connect()
                .execute(f"SELECT {_COLUMNS} FROM memories{where}", params)
                .fetchall()
            )
        scored: list[tuple[float, Any]] = [
            (_cosine(embedding, _from_blob(row[8])), row) for row in rows
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [_row_to_item(row) for _, row in scored[:k]]

    def _recent_sync(
        self, n: int, user_id: str | None, types: Sequence[MemoryType] | None
    ) -> list[MemoryItem]:
        where, params = self._filter_clause(user_id, types)
        with self._lock:
            rows = (
                self._connect()
                .execute(
                    f"SELECT {_COLUMNS} FROM memories{where} ORDER BY created_at DESC LIMIT ?",
                    [*params, n],
                )
                .fetchall()
            )
        return [_row_to_item(row) for row in rows]

    def _get_sync(self, memory_id: str) -> MemoryItem | None:
        with self._lock:
            row = (
                self._connect()
                .execute(f"SELECT {_COLUMNS} FROM memories WHERE id = ?", (memory_id,))
                .fetchone()
            )
        return _row_to_item(row) if row is not None else None

    def _delete_sync(self, memory_id: str) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE memories SET valid = 0 WHERE id = ?", (memory_id,))
            conn.commit()

    def _purge_sync(self, cutoff: str, keep_types: Sequence[MemoryType]) -> int:
        clauses = ["created_at < ?"]
        params: list[Any] = [cutoff]
        if keep_types:
            placeholders = ",".join("?" for _ in keep_types)
            clauses.append(f"type NOT IN ({placeholders})")
            params.extend(t.value for t in keep_types)
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(f"DELETE FROM memories WHERE {' AND '.join(clauses)}", params)
            conn.commit()
            return cursor.rowcount
