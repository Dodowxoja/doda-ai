"""``EventBridge`` testi — obuna, broadcast, tarjima, o'lik-sink izolyatsiyasi."""

from __future__ import annotations

import json
from typing import Any

from doda.core.models.event import Event
from doda.interfaces.api.bridge import EventBridge
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability


class FakeSink:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send(self, message: str) -> None:
        self.messages.append(json.loads(message))


class BoomSink:
    async def send(self, message: str) -> None:
        raise RuntimeError("uzildi")


async def test_register_unregister_count() -> None:
    bridge = EventBridge(AsyncioEventBus())
    a, b = FakeSink(), FakeSink()
    bridge.register(a)
    bridge.register(b)
    assert bridge.client_count == 2
    bridge.unregister(a)
    bridge.unregister(a)  # idempotent
    assert bridge.client_count == 1


async def test_start_forwards_translated_events() -> None:
    bus = AsyncioEventBus()
    bridge = EventBridge(bus)
    sink = FakeSink()
    bridge.register(sink)
    bridge.start()
    await bus.publish(Event(name="thinking.step", payload={"step": "Reja tuzyapman"}))
    assert sink.messages[0]["event"] == "agent.thinking"
    assert sink.messages[0]["data"]["msg"] == "Reja tuzyapman"


async def test_tool_called_fans_out_multiple() -> None:
    bus = AsyncioEventBus()
    bridge = EventBridge(bus)
    sink = FakeSink()
    bridge.register(sink)
    bridge.start()
    await bus.publish(Event(name="tool.called", payload={"name": "files"}))
    events = [m["event"] for m in sink.messages]
    assert "agent.tool_started" in events
    assert "module.status" in events


async def test_broadcast_helper() -> None:
    bridge = EventBridge(AsyncioEventBus())
    sink = FakeSink()
    bridge.register(sink)
    await bridge.broadcast("system.metrics", {"cpu": 30})
    assert sink.messages[0] == {"event": "system.metrics", "data": {"cpu": 30}}


async def test_dead_sink_removed() -> None:
    bridge = EventBridge(AsyncioEventBus(), observability=BasicObservability())
    good, bad = FakeSink(), BoomSink()
    bridge.register(good)
    bridge.register(bad)
    await bridge.broadcast("x", {"a": 1})
    assert bridge.client_count == 1  # bad chiqarildi
    assert good.messages  # good baribir oldi


async def test_stop_unsubscribes() -> None:
    bus = AsyncioEventBus()
    bridge = EventBridge(bus)
    sink = FakeSink()
    bridge.register(sink)
    bridge.start()
    bridge.stop()
    await bus.publish(Event(name="thinking.step", payload={"step": "x"}))
    assert sink.messages == []  # obuna bekor qilingan
