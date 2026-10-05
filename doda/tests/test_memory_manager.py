"""``MemoryManager`` testlari — remember / recall / profile / forget."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from code.doda.agent import MemoryManager
from code.doda.core.models.memory import MemoryItem, MemoryType
from code.doda.providers.memory import HashingEmbedding, SQLiteMemoryStore


def _manager(tmp_path: Path) -> tuple[MemoryManager, SQLiteMemoryStore, HashingEmbedding]:
    store = SQLiteMemoryStore(tmp_path / "memory.db")
    embedder = HashingEmbedding()
    return MemoryManager(store, embedder), store, embedder


async def test_remember_then_recall_finds_relevant(tmp_path: Path) -> None:
    manager, _, _ = _manager(tmp_path)
    await manager.remember("Men Flutter dasturchisiman", MemoryType.PREFERENCE)
    await manager.remember("Bugun ob-havo issiq", MemoryType.FACT)
    results = await manager.recall("Flutter", k=1)
    assert len(results) == 1
    assert "Flutter" in results[0].content


async def test_profile_returns_only_preferences(tmp_path: Path) -> None:
    manager, _, _ = _manager(tmp_path)
    await manager.remember("Qorong'i rejimni yoqtiraman", MemoryType.PREFERENCE)
    await manager.remember("Oddiy fakt", MemoryType.FACT)
    profile = await manager.profile()
    assert [item.type for item in profile] == [MemoryType.PREFERENCE]


async def test_forget_removes_old_but_keeps_protected(tmp_path: Path) -> None:
    manager, store, embedder = _manager(tmp_path)
    old_fact = MemoryItem(
        id="old",
        content="eski fakt",
        type=MemoryType.FACT,
        created_at=datetime(2000, 1, 1, tzinfo=UTC),
    )
    old_pref = MemoryItem(
        id="pref",
        content="eski afzallik",
        type=MemoryType.PREFERENCE,
        created_at=datetime(2000, 1, 1, tzinfo=UTC),
    )
    await store.add(old_fact, await embedder.embed(old_fact.content))
    await store.add(old_pref, await embedder.embed(old_pref.content))

    removed = await manager.forget(older_than_days=30)
    assert removed == 1  # FACT o'chdi
    assert await store.get("pref") is not None  # PREFERENCE saqlandi
