"""``MemoryStore`` porti uchun contract — har qanday implementatsiya bajarishi shart."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from doda.core.interfaces.memory import MemoryStore
from doda.core.models.memory import MemoryItem, MemoryType


class MemoryStoreContract:
    """MemoryStore kelishuvi (subklass ``make_store()``ni beradi)."""

    def make_store(self, tmp_path: Path) -> MemoryStore:
        raise NotImplementedError

    async def test_add_and_get(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        item = MemoryItem.create("salom", MemoryType.FACT)
        await store.add(item, [1.0, 0.0])
        fetched = await store.get(item.id)
        assert fetched is not None
        assert fetched.content == "salom"
        assert fetched.type is MemoryType.FACT

    async def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        assert await store.get("yoq") is None

    async def test_search_orders_by_similarity(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        near = MemoryItem.create("near", MemoryType.FACT)
        far = MemoryItem.create("far", MemoryType.FACT)
        await store.add(near, [1.0, 0.0])
        await store.add(far, [0.0, 1.0])
        results = await store.search([1.0, 0.0], k=2)
        assert results[0].id == near.id

    async def test_recent_orders_by_time(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        old = MemoryItem(
            id="old",
            content="old",
            type=MemoryType.FACT,
            created_at=datetime(2000, 1, 1, tzinfo=UTC),
        )
        new = MemoryItem(
            id="new",
            content="new",
            type=MemoryType.FACT,
            created_at=datetime(2030, 1, 1, tzinfo=UTC),
        )
        await store.add(old, [1.0])
        await store.add(new, [1.0])
        results = await store.recent(2)
        assert results[0].id == "new"

    async def test_delete_excludes_from_search(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        item = MemoryItem.create("bor", MemoryType.FACT)
        await store.add(item, [1.0, 0.0])
        await store.delete(item.id)
        results = await store.search([1.0, 0.0], k=5)
        assert all(result.id != item.id for result in results)

    async def test_filter_by_type(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        fact = MemoryItem.create("fakt", MemoryType.FACT)
        pref = MemoryItem.create("afzallik", MemoryType.PREFERENCE)
        await store.add(fact, [1.0])
        await store.add(pref, [1.0])
        results = await store.search([1.0], k=5, types=[MemoryType.PREFERENCE])
        assert [r.id for r in results] == [pref.id]

    async def test_filter_by_user(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        mine = MemoryItem.create("meniki", MemoryType.FACT, user_id="me")
        other = MemoryItem.create("boshqa", MemoryType.FACT, user_id="other")
        await store.add(mine, [1.0])
        await store.add(other, [1.0])
        results = await store.recent(5, user_id="me")
        assert [r.id for r in results] == [mine.id]

    async def test_purge_older_than(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        old = MemoryItem(
            id="old",
            content="eski",
            type=MemoryType.FACT,
            created_at=datetime(2000, 1, 1, tzinfo=UTC),
        )
        new = MemoryItem(
            id="new",
            content="yangi",
            type=MemoryType.FACT,
            created_at=datetime(2030, 1, 1, tzinfo=UTC),
        )
        await store.add(old, [1.0])
        await store.add(new, [1.0])
        removed = await store.purge_older_than("2020-01-01T00:00:00+00:00")
        assert removed == 1
        assert await store.get("old") is None
        assert await store.get("new") is not None

    async def test_purge_keeps_types(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        pref = MemoryItem(
            id="p",
            content="afzallik",
            type=MemoryType.PREFERENCE,
            created_at=datetime(2000, 1, 1, tzinfo=UTC),
        )
        await store.add(pref, [1.0])
        removed = await store.purge_older_than(
            "2020-01-01T00:00:00+00:00", keep_types=[MemoryType.PREFERENCE]
        )
        assert removed == 0
        assert await store.get("p") is not None
