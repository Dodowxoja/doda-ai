"""``Scheduler`` testi — schedule/tick/cancel + takroriy vazifa + eventlar."""

from __future__ import annotations

from datetime import datetime, timedelta

from code.doda.core.models.event import Event
from code.doda.core.models.task import TaskStatus
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.observability import BasicObservability
from code.doda.providers.scheduler import InMemoryTaskStore
from code.doda.scheduler import Scheduler

_NOW = datetime(2026, 8, 9, 12, 0, 0)


class FakeAgent:
    def __init__(self) -> None:
        self.handled: list[str] = []

    async def handle(self, user_text: str) -> str:
        self.handled.append(user_text)
        return "ok"


def _make(store: InMemoryTaskStore | None = None, agent: FakeAgent | None = None) -> Scheduler:
    return Scheduler(
        store or InMemoryTaskStore(),
        agent or FakeAgent(),
        AsyncioEventBus(),
        now=lambda: _NOW,
        observability=BasicObservability(),
    )


async def test_schedule_creates_pending_task() -> None:
    store = InMemoryTaskStore()
    scheduler = _make(store)
    task = await scheduler.schedule("eslatma", _NOW + timedelta(minutes=5))
    assert task.status == TaskStatus.PENDING
    assert (await store.get(task.id)) is not None


async def test_tick_fires_due_task_via_agent() -> None:
    store = InMemoryTaskStore()
    agent = FakeAgent()
    scheduler = _make(store, agent)
    task = await scheduler.schedule("suv ich", _NOW - timedelta(seconds=1))
    fired = await scheduler.tick()
    assert fired == 1
    assert agent.handled == ["suv ich"]
    done = await store.get(task.id)
    assert done is not None
    assert done.status == TaskStatus.DONE


async def test_tick_ignores_future_task() -> None:
    scheduler = _make()
    await scheduler.schedule("keyin", _NOW + timedelta(minutes=10))
    assert await scheduler.tick() == 0


async def test_recurring_task_is_rescheduled() -> None:
    store = InMemoryTaskStore()
    scheduler = _make(store)
    task = await scheduler.schedule(
        "har daqiqa", _NOW - timedelta(seconds=1), interval_seconds=60.0
    )
    await scheduler.tick()
    updated = await store.get(task.id)
    assert updated is not None
    assert updated.status == TaskStatus.PENDING  # takroriy → hali kutmoqda
    assert updated.run_at == _NOW + timedelta(seconds=60)


async def test_cancel_pending_task() -> None:
    store = InMemoryTaskStore()
    scheduler = _make(store)
    task = await scheduler.schedule("bekor", _NOW + timedelta(minutes=1))
    assert await scheduler.cancel(task.id) is True
    cancelled = await store.get(task.id)
    assert cancelled is not None
    assert cancelled.status == TaskStatus.CANCELLED
    assert await scheduler.tick() == 0  # bekor qilingan ishlamaydi


async def test_cancel_missing_returns_false() -> None:
    assert await _make().cancel("yoq") is False


async def test_cancel_non_pending_returns_false() -> None:
    store = InMemoryTaskStore()
    scheduler = _make(store)
    task = await scheduler.schedule("bir marta", _NOW - timedelta(seconds=1))
    await scheduler.tick()  # DONE bo'ladi
    assert await scheduler.cancel(task.id) is False


async def test_emits_task_events() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    for name in ("task.scheduled", "task.fired", "task.completed"):
        events.subscribe(name, handler)
    scheduler = Scheduler(InMemoryTaskStore(), FakeAgent(), events, now=lambda: _NOW)
    await scheduler.schedule("ish", _NOW - timedelta(seconds=1))
    await scheduler.tick()
    assert seen == ["task.scheduled", "task.fired", "task.completed"]
