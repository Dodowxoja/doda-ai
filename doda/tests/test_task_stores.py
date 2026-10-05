"""Vazifa omborlari testlari — contract (SQLite + xotira) + SQLite persistensiyasi."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from doda.core.interfaces.scheduler import TaskStore
from doda.core.models.task import ScheduledTask
from doda.providers.scheduler import InMemoryTaskStore, SQLiteTaskStore
from doda.tests.contracts.task_store_contract import TaskStoreContract


class TestInMemoryTaskStore(TaskStoreContract):
    def make_store(self) -> TaskStore:
        return InMemoryTaskStore()


class TestSQLiteTaskStore(TaskStoreContract):
    def make_store(self) -> TaskStore:
        return SQLiteTaskStore(Path(self._tmp.name) / "tasks.db")

    def setup_method(self) -> None:
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()

    def teardown_method(self) -> None:
        self._tmp.cleanup()


async def test_sqlite_persists_across_reconnect(tmp_path: Path) -> None:
    path = tmp_path / "tasks.db"
    store = SQLiteTaskStore(path)
    now = datetime(2026, 8, 9, 12, 0, 0)
    await store.add(ScheduledTask(id="a", prompt="eslatma", run_at=now, interval_seconds=60.0))
    store.close()

    reopened = SQLiteTaskStore(path)
    fetched = await reopened.get("a")
    assert fetched is not None
    assert fetched.prompt == "eslatma"
    assert fetched.interval_seconds == 60.0
    assert fetched.is_recurring
    reopened.close()
