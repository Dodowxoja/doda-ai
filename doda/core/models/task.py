"""Rejalashtirilgan vazifa domen modeli — ``ScheduledTask`` (vazifalar + eslatmalar).

Bir martalik yoki takroriy (``interval_seconds > 0``) vazifa. Vaqti kelganda ``Scheduler``
uni ishga tushiradi (``prompt`` Agentga beriladi). Model o'zgarmas (frozen) — domen sof.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    """Vazifa holati."""

    PENDING = "pending"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """Belgilangan vaqtda bajariladigan vazifa (yoki eslatma)."""

    id: str
    prompt: str
    run_at: datetime
    interval_seconds: float = 0.0
    status: TaskStatus = TaskStatus.PENDING

    @property
    def is_recurring(self) -> bool:
        """Takroriy vazifami (interval musbat bo'lsa)."""
        return self.interval_seconds > 0
