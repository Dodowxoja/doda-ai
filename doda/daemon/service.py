"""``DaemonService`` — DODA'ning 24/7 doimiy ishlash supervizori.

Ishga tushganda pluginlarni yuklaydi va fon-siklini boshlaydi (davriy ``scheduler.tick`` —
vaqti kelgan vazifa/eslatmalarni bajaradi). To'xtaganda pluginlarni tozalaydi. Xatolar
izolyatsiya qilinadi (bitta tick xatosi daemonni yiqitmaydi). ``daemon.*`` eventlari chiqadi.

OS-servis (launchd/systemd) o'rnatish — paketlash mavzusi (``packaging/``); bu yerda esa
sof boshqaruv mantiqi (deterministik test uchun ``sleep`` inject qilinadi).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.observability import Observability
from doda.core.models.event import Event
from doda.plugins import PluginManager
from doda.scheduler import Scheduler

_SOURCE = "daemon"

Sleep = Callable[[float], Awaitable[None]]
"""Kutish funksiyasi turi (test uchun almashtiriladi)."""


async def _default_sleep(seconds: float) -> None:  # pragma: no cover
    import asyncio

    await asyncio.sleep(seconds)


class DaemonService:
    """Fon-sikllarini va plugin hayot-siklini boshqaruvchi supervizor."""

    def __init__(
        self,
        scheduler: Scheduler,
        plugins: PluginManager,
        events: EventBus,
        *,
        tick_interval: float = 1.0,
        sleep: Sleep = _default_sleep,
        observability: Observability | None = None,
    ) -> None:
        """Daemonni portlar bilan quradi (DI).

        Args:
            scheduler: Vazifalarni bajaruvchi (har tickda ``tick`` chaqiriladi).
            plugins: Ishga tushishda yuklanadigan / to'xtashda tozalanadigan pluginlar.
            events: ``daemon.*`` eventlari uchun avtobus.
            tick_interval: Ticklar orasidagi kutish (soniya).
            sleep: Kutish funksiyasi (test uchun almashtiriladi).
            observability: Ixtiyoriy — loglash uchun.
        """
        self._scheduler = scheduler
        self._plugins = plugins
        self._events = events
        self._tick_interval = tick_interval
        self._sleep = sleep
        self._obs = observability
        self._running = False

    @property
    def is_running(self) -> bool:
        """Daemon hozir ishlayaptimi."""
        return self._running

    async def start(self) -> None:
        """Pluginlarni yuklaydi va daemonni ishga tayyorlaydi."""
        await self._plugins.setup_all()
        self._running = True
        await self._emit("daemon.started")

    async def stop(self) -> None:
        """Daemonni to'xtatadi va pluginlarni tozalaydi."""
        self._running = False
        await self._plugins.teardown_all()
        await self._emit("daemon.stopped")

    async def tick_once(self) -> int:
        """Bitta fon-tsiklini bajaradi (scheduler); xato izolyatsiya qilinadi."""
        try:
            fired = await self._scheduler.tick()
        except Exception as exc:  # bitta tick xatosi daemonni yiqitmasin
            if self._obs is not None:
                self._obs.log("error", "daemon tick xato berdi", error=repr(exc))
            await self._emit("daemon.tick_error")
            return 0
        await self._emit("daemon.tick")
        return fired

    async def run(self, *, max_ticks: int | None = None) -> None:
        """Daemonni ishga tushiradi va fon-siklini yuritadi (to'xtaguncha).

        Args:
            max_ticks: Test uchun — shu miqdor tickdan so'ng to'xtaydi (None = cheksiz).
        """
        await self.start()
        ticks = 0
        try:
            while self._running:
                await self.tick_once()
                ticks += 1
                if max_ticks is not None and ticks >= max_ticks:
                    break
                await self._sleep(self._tick_interval)
        finally:
            await self.stop()

    async def _emit(self, name: str) -> None:
        await self._events.publish(Event(name=name, source=_SOURCE))
