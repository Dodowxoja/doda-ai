"""``TaskStore`` porti — rejalashtirilgan vazifalarni saqlash.

``Scheduler`` (M9) shu port orqali vazifalarni saqlaydi/o'qiydi. Konkret implementatsiya
(SQLite) ``doda/providers/scheduler/`` da; port DB'ni abstraktlaydi (ADR-007).
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from code.doda.core.models.task import ScheduledTask


@runtime_checkable
class TaskStore(Protocol):
    """Rejalashtirilgan vazifalar ombori."""

    async def add(self, task: ScheduledTask) -> None:
        """Vazifani saqlaydi (yoki mavjudini yangilaydi)."""
        ...

    async def get(self, task_id: str) -> ScheduledTask | None:
        """``task_id`` bo'yicha vazifani qaytaradi; topilmasa ``None``."""
        ...

    async def due(self, now: datetime) -> tuple[ScheduledTask, ...]:
        """Vaqti kelgan (``run_at <= now``) PENDING vazifalarni qaytaradi."""
        ...

    async def list_pending(self) -> tuple[ScheduledTask, ...]:
        """Barcha kutayotgan (PENDING) vazifalarni qaytaradi."""
        ...
