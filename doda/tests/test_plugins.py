"""Plugin tizimi testlari — PluginManager hayot-sikli + DefaultPluginContext ulanishi."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from doda.core.interfaces.plugin import PluginContext
from doda.core.models.event import Event
from doda.plugins import DefaultPluginContext, PluginManager
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability
from doda.tools import ToolRegistry


class _EchoTool:
    @property
    def name(self) -> str:
        return "echo"

    @property
    def description(self) -> str:
        return "aks-sado"

    @property
    def parameters(self) -> Mapping[str, Any]:
        return {"type": "object", "properties": {}}

    async def run(self, arguments: Mapping[str, Any]) -> str:
        return "echo"


class GoodPlugin:
    """Asbob ro'yxatga oluvchi va hodisaga obuna bo'luvchi soxta plugin."""

    def __init__(self, name: str = "good") -> None:
        self._name = name
        self.torn_down = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return "1.0.0"

    async def setup(self, context: PluginContext) -> None:
        context.register_tool(_EchoTool())
        context.subscribe("x", self._on_x)

    async def teardown(self) -> None:
        self.torn_down = True

    async def _on_x(self, event: Event) -> None:
        pass


class BoomPlugin(GoodPlugin):
    async def setup(self, context: PluginContext) -> None:
        raise RuntimeError("portladi")


def _context() -> tuple[DefaultPluginContext, ToolRegistry, AsyncioEventBus]:
    tools = ToolRegistry()
    events = AsyncioEventBus()
    return DefaultPluginContext(tools, events), tools, events


def test_register_duplicate_raises() -> None:
    context, _, events = _context()
    manager = PluginManager(context, events, [GoodPlugin()])
    with pytest.raises(ValueError, match="allaqachon"):
        manager.register(GoodPlugin())


def test_names() -> None:
    context, _, events = _context()
    manager = PluginManager(context, events, [GoodPlugin("a"), GoodPlugin("b")])
    assert manager.names() == ("a", "b")


async def test_setup_registers_tool_and_subscription() -> None:
    context, tools, events = _context()
    manager = PluginManager(context, events, [GoodPlugin()])
    await manager.setup_all()
    assert "echo" in {spec.name for spec in tools.specs()}
    assert len(context.subscriptions) == 1


async def test_setup_emits_loaded_event() -> None:
    context, _, events = _context()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.payload["name"])

    events.subscribe("plugin.loaded", handler)
    await PluginManager(context, events, [GoodPlugin()]).setup_all()
    assert seen == ["good"]


async def test_failing_plugin_is_isolated() -> None:
    context, tools, events = _context()
    failed: list[str] = []

    async def handler(event: Event) -> None:
        failed.append(event.payload["name"])

    events.subscribe("plugin.failed", handler)
    manager = PluginManager(
        context, events, [BoomPlugin("bad"), GoodPlugin("ok")], observability=BasicObservability()
    )
    await manager.setup_all()
    assert failed == ["bad"]
    assert "echo" in {spec.name for spec in tools.specs()}  # yaxshi plugin baribir yuklandi


async def test_teardown_only_active_plugins() -> None:
    context, _, events = _context()
    good = GoodPlugin("ok")
    manager = PluginManager(context, events, [BoomPlugin("bad"), good])
    await manager.setup_all()
    await manager.teardown_all()
    assert good.torn_down is True


async def test_context_register_tool_and_subscribe() -> None:
    context, tools, _ = _context()
    context.register_tool(_EchoTool())
    assert "echo" in {spec.name for spec in tools.specs()}
    context.subscribe("y", GoodPlugin()._on_x)
    assert len(context.subscriptions) == 1
