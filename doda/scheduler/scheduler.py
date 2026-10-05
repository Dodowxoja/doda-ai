"""``Scheduler`` — vaqti kelgan vazifalarni ishga tushiradi (vazifalar + eslatmalar).

``tick(now)`` vaqti kelgan vazifalarni topib, har birini Agent orqali bajaradi (``task.fired``
/``task.completed`` eventlari). Takroriy vazifa qayta rejalashtiriladi, bir martalik esa DONE
bo'ladi. Doimiy sikl (``run_forever``) M12 (Daemon) da ``tick`` ni takrorlaydi.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from doda.core.interfaces.agent import Agent
from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.observability import Observability
from doda.core.interfaces.scheduler import TaskStore
from doda.core.models.event import Event
from doda.core.models.task import ScheduledTask, TaskStatus

_SOURCE = "scheduler"


class Scheduler:
    """Vazifalarni saqlaydi va vaqti kelganda ishga tushiradi."""

    def __init__(
        self,
        store: TaskStore,
        executor: Agent,
        events: EventBus,
        *,
        now: Callable[[], datetime] = datetime.now,
        observability: Observability | None = None,
    ) -> None:
        """Schedulerni portlar bilan quradi (DI).

        Args:
            store: Vazifalar ombori.
            executor: Vazifa ``prompt``ini bajaruvchi agent (M4 tool-loop).
            events: ``task.*`` eventlari uchun avtobus.
            now: Joriy vaqt manbai (test uchun almashtiriladi).
            observability: Ixtiyoriy — loglash uchun.
        """
        self._store = store
        self._executor = executor
        self._events = events
        self._now = now
        self._obs = observability

    async def schedule(
        self, prompt: str, run_at: datetime, *, interval_seconds: float = 0.0
    ) -> ScheduledTask:
        """Yangi vazifa (yoki eslatma) rejalashtiradi va uni qaytaradi."""
        task = ScheduledTask(
            id=uuid4().hex, prompt=prompt, run_at=run_at, interval_seconds=interval_seconds
        )
        await self._store.add(task)
        await self._emit("task.scheduled", {"id": task.id, "prompt": prompt})
        return task

    async def cancel(self, task_id: str) -> bool:
        """Vazifani bekor qiladi; topilib bekor qilinsa ``True``."""
        task = await self._store.get(task_id)
        if task is None or task.status != TaskStatus.PENDING:
            return False
        await self._store.add(replace(task, status=TaskStatus.CANCELLED))
        await self._emit("task.cancelled", {"id": task_id})
        return True

    async def tick(self, now: datetime | None = None) -> int:
        """Vaqti kelgan vazifalarni bajaradi; bajarilganlar sonini qaytaradi."""
        current = now if now is not None else self._now()
        fired = 0
        for task in await self._store.due(current):
            await self._emit("task.fired", {"id": task.id, "prompt": task.prompt})
            await self._executor.handle(task.prompt)
            await self._reschedule_or_finish(task, current)
            await self._emit("task.completed", {"id": task.id})
            fired += 1
        return fired

    async def _reschedule_or_finish(self, task: ScheduledTask, current: datetime) -> None:
        """Takroriy vazifani keyingi vaqtga suradi, bir martalikni DONE qiladi."""
        if task.is_recurring:
            next_run = current + timedelta(seconds=task.interval_seconds)
            await self._store.add(replace(task, run_at=next_run))
        else:
            await self._store.add(replace(task, status=TaskStatus.DONE))

    async def _emit(self, name: str, payload: Mapping[str, Any]) -> None:
        await self._events.publish(Event(name=name, payload=payload, source=_SOURCE))
        if self._obs is not None:
            self._obs.log("debug", f"scheduler event: {name}")
