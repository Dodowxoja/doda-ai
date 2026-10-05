"""``InMemoryTaskStore`` — TaskStore portining xotira-ichi (DB'siz) implementatsiyasi.

Test va yengil ishlatishlar uchun; jarayon qayta ishga tushsa yo'qoladi. Doimiy saqlash
kerak bo'lsa ``SQLiteTaskStore`` ishlatiladi (bir xil port).
"""

from __future__ import annotations

from datetime import datetime

from doda.core.models.task import ScheduledTask, TaskStatus


class InMemoryTaskStore:
    """Vazifalarni oddiy lug'atda saqlaydigan ombor."""

    def __init__(self) -> None:
        self._tasks: dict[str, ScheduledTask] = {}

    async def add(self, task: ScheduledTask) -> None:
        self._tasks[task.id] = task

    async def get(self, task_id: str) -> ScheduledTask | None:
        return self._tasks.get(task_id)

    async def due(self, now: datetime) -> tuple[ScheduledTask, ...]:
        due = [
            task
            for task in self._tasks.values()
            if task.status == TaskStatus.PENDING and task.run_at <= now
        ]
        due.sort(key=lambda task: task.run_at)
        return tuple(due)

    async def list_pending(self) -> tuple[ScheduledTask, ...]:
        pending = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        pending.sort(key=lambda task: task.run_at)
        return tuple(pending)
