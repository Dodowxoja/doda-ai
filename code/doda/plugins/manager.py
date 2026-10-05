"""``PluginManager`` — pluginlarni ro'yxatga oladi va hayot-siklini boshqaradi.

``setup_all`` har bir pluginni ishga tayyorlaydi (xato bersa izolyatsiya qilinadi — bitta
plugin xatosi boshqalarini to'xtatmaydi). ``plugin.*`` eventlari chiqadi. Hot-reload v1.1 ga
qoldirildi (docs/PLUGINS.md).
"""

from __future__ import annotations

from collections.abc import Iterable

from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.interfaces.plugin import Plugin, PluginContext
from code.doda.core.models.event import Event

_SOURCE = "plugins"


class PluginManager:
    """Pluginlar registri + hayot-sikl boshqaruvi."""

    def __init__(
        self,
        context: PluginContext,
        events: EventBus,
        plugins: Iterable[Plugin] = (),
        *,
        observability: Observability | None = None,
    ) -> None:
        """Managerni konteks va (ixtiyoriy) boshlang'ich pluginlar bilan quradi.

        Args:
            context: Pluginlar o'zini ro'yxatga oladigan konteks.
            events: ``plugin.*`` eventlari uchun avtobus.
            plugins: Boshlang'ich pluginlar (nomi noyob bo'lishi shart).
            observability: Ixtiyoriy — loglash uchun.
        """
        self._context = context
        self._events = events
        self._obs = observability
        self._plugins: dict[str, Plugin] = {}
        self._active: list[Plugin] = []
        for plugin in plugins:
            self.register(plugin)

    def register(self, plugin: Plugin) -> None:
        """Pluginni ro'yxatga qo'shadi (hali setup qilmaydi).

        Raises:
            ValueError: Shu nomli plugin allaqachon mavjud.
        """
        if plugin.name in self._plugins:
            raise ValueError(f"Plugin '{plugin.name}' allaqachon ro'yxatdan o'tgan")
        self._plugins[plugin.name] = plugin

    def names(self) -> tuple[str, ...]:
        """Ro'yxatdan o'tgan plugin nomlari."""
        return tuple(self._plugins)

    async def setup_all(self) -> None:
        """Barcha pluginlarni ishga tayyorlaydi (xatolar izolyatsiya qilinadi)."""
        for plugin in self._plugins.values():
            try:
                await plugin.setup(self._context)
            except Exception as exc:  # bitta plugin xatosi boshqalarini to'xtatmasin
                if self._obs is not None:
                    self._obs.log("error", f"plugin '{plugin.name}' yuklanmadi", error=repr(exc))
                await self._emit("plugin.failed", {"name": plugin.name, "error": repr(exc)})
                continue
            self._active.append(plugin)
            await self._emit("plugin.loaded", {"name": plugin.name, "version": plugin.version})

    async def teardown_all(self) -> None:
        """Yuklangan pluginlarni tozalaydi (teardown)."""
        for plugin in self._active:
            await plugin.teardown()
            await self._emit("plugin.unloaded", {"name": plugin.name})
        self._active.clear()

    async def _emit(self, name: str, payload: dict[str, str]) -> None:
        await self._events.publish(Event(name=name, payload=payload, source=_SOURCE))
