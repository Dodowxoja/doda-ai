"""``SQLiteMemoryStore`` testlari — MemoryStore contract + persistence."""

from __future__ import annotations

from pathlib import Path

from code.doda.core.interfaces.memory import MemoryStore
from code.doda.core.models.memory import MemoryItem, MemoryType
from code.doda.providers.memory import SQLiteMemoryStore
from code.doda.tests.contracts.memory_store_contract import MemoryStoreContract


class TestSQLiteMemoryStore(MemoryStoreContract):
    def make_store(self, tmp_path: Path) -> MemoryStore:
        return SQLiteMemoryStore(tmp_path / "memory.db")

    async def test_persists_across_reconnect(self, tmp_path: Path) -> None:
        path = tmp_path / "memory.db"
        item = MemoryItem.create("saqlanadi", MemoryType.FACT)
        await SQLiteMemoryStore(path).add(item, [1.0, 0.0])

        reopened = SQLiteMemoryStore(path)  # yangi ulanish, o'sha fayl
        fetched = await reopened.get(item.id)
        assert fetched is not None
        assert fetched.content == "saqlanadi"

    async def test_close_then_reuse_reconnects(self, tmp_path: Path) -> None:
        store = SQLiteMemoryStore(tmp_path / "memory.db")
        item = MemoryItem.create("x", MemoryType.FACT)
        await store.add(item, [1.0])
        store.close()  # ulanishni yopadi
        store.close()  # ikkinchi marta — xavfsiz (idempotent)
        fetched = await store.get(item.id)  # qayta ulanadi
        assert fetched is not None
