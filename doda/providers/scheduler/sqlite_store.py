"""``SQLiteTaskStore`` — TaskStore portining stdlib ``sqlite3`` implementatsiyasi.

M3 xotira-saqlagichi bilan bir xil naqsh: lazy ulanish + ``Lock`` + ``asyncio.to_thread``
(Async-First), ``close()``/``__del__`` bilan resurs sizishining oldi olinadi.
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from doda.core.models.task import ScheduledTask, TaskStatus

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id       TEXT PRIMARY KEY,
    prompt   TEXT NOT NULL,
    run_at   TEXT NOT NULL,
    interval REAL NOT NULL,
    status   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tasks_due ON tasks (status, run_at);
"""

_COLUMNS = "id, prompt, run_at, interval, status"


def _row_to_task(row: Any) -> ScheduledTask:
    return ScheduledTask(
        id=str(row[0]),
        prompt=str(row[1]),
        run_at=datetime.fromisoformat(str(row[2])),
        interval_seconds=float(row[3]),
        status=TaskStatus(str(row[4])),
    )


class SQLiteTaskStore:
    """SQLite asosidagi vazifa ombori (ulanish lazy quriladi)."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.Lock()

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
        conn = getattr(self, "_conn", None)
        if conn is not None:
            with suppress(Exception):
                conn.close()

    # ---- async port metodlari ----
    async def add(self, task: ScheduledTask) -> None:
        await asyncio.to_thread(self._add_sync, task)

    async def get(self, task_id: str) -> ScheduledTask | None:
        return await asyncio.to_thread(self._get_sync, task_id)

    async def due(self, now: datetime) -> tuple[ScheduledTask, ...]:
        return await asyncio.to_thread(self._due_sync, now)

    async def list_pending(self) -> tuple[ScheduledTask, ...]:
        return await asyncio.to_thread(self._list_pending_sync)

    # ---- sinxron amallar (thread ichida, lock bilan) ----
    def _add_sync(self, task: ScheduledTask) -> None:
        with self._lock:
            conn = self._connect()
            conn.execute(
                f"INSERT OR REPLACE INTO tasks ({_COLUMNS}) VALUES (?,?,?,?,?)",
                (
                    task.id,
                    task.prompt,
                    task.run_at.isoformat(),
                    task.interval_seconds,
                    task.status.value,
                ),
            )
            conn.commit()

    def _get_sync(self, task_id: str) -> ScheduledTask | None:
        with self._lock:
            row = (
                self._connect()
                .execute(f"SELECT {_COLUMNS} FROM tasks WHERE id = ?", (task_id,))
                .fetchone()
            )
        return _row_to_task(row) if row is not None else None

    def _due_sync(self, now: datetime) -> tuple[ScheduledTask, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute(
                    f"SELECT {_COLUMNS} FROM tasks "
                    "WHERE status = ? AND run_at <= ? ORDER BY run_at",
                    (TaskStatus.PENDING.value, now.isoformat()),
                )
                .fetchall()
            )
        return tuple(_row_to_task(row) for row in rows)

    def _list_pending_sync(self) -> tuple[ScheduledTask, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute(
                    f"SELECT {_COLUMNS} FROM tasks WHERE status = ? ORDER BY run_at",
                    (TaskStatus.PENDING.value,),
                )
                .fetchall()
            )
        return tuple(_row_to_task(row) for row in rows)
