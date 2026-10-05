"""``TaskStore`` porti uchun contract-test bazasi.

Har bir konkret ombor ``make_store()`` beradi va shu umumiy tekshiruvlarni meros oladi
(add/get/due/list_pending + status filtri).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from code.doda.core.interfaces.scheduler import TaskStore
from code.doda.core.models.task import ScheduledTask, TaskStatus


class TaskStoreContract:
    """Barcha ``TaskStore`` implementatsiyalari qanoatlantirishi shart bo'lgan shartlar."""

    def make_store(self) -> TaskStore:
        raise NotImplementedError

    def _task(
        self, task_id: str, run_at: datetime, status: TaskStatus = TaskStatus.PENDING
    ) -> ScheduledTask:
        return ScheduledTask(id=task_id, prompt="ish", run_at=run_at, status=status)

    async def test_add_and_get(self) -> None:
        store = self.make_store()
        now = datetime(2026, 8, 9, 12, 0, 0)
        await store.add(self._task("a", now))
        fetched = await store.get("a")
        assert fetched is not None
        assert fetched.id == "a"

    async def test_get_missing_returns_none(self) -> None:
        assert await self.make_store().get("yoq") is None

    async def test_add_replaces_existing(self) -> None:
        store = self.make_store()
        now = datetime(2026, 8, 9, 12, 0, 0)
        await store.add(self._task("a", now))
        await store.add(self._task("a", now, status=TaskStatus.DONE))
        fetched = await store.get("a")
        assert fetched is not None
        assert fetched.status == TaskStatus.DONE

    async def test_due_returns_only_past_pending(self) -> None:
        store = self.make_store()
        base = datetime(2026, 8, 9, 12, 0, 0)
        await store.add(self._task("past", base - timedelta(minutes=1)))
        await store.add(self._task("future", base + timedelta(minutes=1)))
        await store.add(self._task("done", base - timedelta(minutes=1), status=TaskStatus.DONE))
        due = await store.due(base)
        assert [t.id for t in due] == ["past"]

    async def test_list_pending_excludes_finished(self) -> None:
        store = self.make_store()
        base = datetime(2026, 8, 9, 12, 0, 0)
        await store.add(self._task("p", base))
        await store.add(self._task("d", base, status=TaskStatus.DONE))
        pending = await store.list_pending()
        assert [t.id for t in pending] == ["p"]
