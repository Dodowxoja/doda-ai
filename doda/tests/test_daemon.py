"""``DaemonService`` testi — start/stop hayot-sikli, tick sikli, xato izolyatsiyasi."""

from __future__ import annotations

from doda.core.models.event import Event
from doda.daemon import DaemonService
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability


class FakeScheduler:
    def __init__(self, *, fail: bool = False) -> None:
        self.ticks = 0
        self._fail = fail

    async def tick(self, now: object = None) -> int:
        self.ticks += 1
        if self._fail:
            raise RuntimeError("tick portladi")
        return 1


class FakePlugins:
    def __init__(self) -> None:
        self.setup_called = 0
        self.teardown_called = 0

    async def setup_all(self) -> None:
        self.setup_called += 1

    async def teardown_all(self) -> None:
        self.teardown_called += 1


async def _noop_sleep(seconds: float) -> None:
    pass


def _daemon(scheduler: object, plugins: object, events: AsyncioEventBus) -> DaemonService:
    return DaemonService(
        scheduler,  # type: ignore[arg-type]
        plugins,  # type: ignore[arg-type]
        events,
        sleep=_noop_sleep,
    )


async def test_start_loads_plugins_and_sets_running() -> None:
    plugins = FakePlugins()
    daemon = _daemon(FakeScheduler(), plugins, AsyncioEventBus())
    await daemon.start()
    assert daemon.is_running is True
    assert plugins.setup_called == 1


async def test_stop_tears_down_plugins() -> None:
    plugins = FakePlugins()
    daemon = _daemon(FakeScheduler(), plugins, AsyncioEventBus())
    await daemon.start()
    await daemon.stop()
    assert daemon.is_running is False
    assert plugins.teardown_called == 1


async def test_tick_once_runs_scheduler() -> None:
    scheduler = FakeScheduler()
    daemon = _daemon(scheduler, FakePlugins(), AsyncioEventBus())
    assert await daemon.tick_once() == 1
    assert scheduler.ticks == 1


async def test_tick_once_isolates_errors() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    events.subscribe("daemon.tick_error", handler)
    daemon = DaemonService(
        FakeScheduler(fail=True),  # type: ignore[arg-type]
        FakePlugins(),  # type: ignore[arg-type]
        events,
        sleep=_noop_sleep,
        observability=BasicObservability(),
    )
    assert await daemon.tick_once() == 0  # xato → 0, daemon yiqilmaydi
    assert "daemon.tick_error" in seen


async def test_run_loops_bounded_and_lifecycle() -> None:
    scheduler = FakeScheduler()
    plugins = FakePlugins()
    daemon = _daemon(scheduler, plugins, AsyncioEventBus())
    await daemon.run(max_ticks=3)
    assert scheduler.ticks == 3
    assert plugins.setup_called == 1
    assert plugins.teardown_called == 1
    assert daemon.is_running is False


async def test_run_emits_lifecycle_events() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    for name in ("daemon.started", "daemon.tick", "daemon.stopped"):
        events.subscribe(name, handler)
    await _daemon(FakeScheduler(), FakePlugins(), events).run(max_ticks=1)
    assert seen == ["daemon.started", "daemon.tick", "daemon.stopped"]
