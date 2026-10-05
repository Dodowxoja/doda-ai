"""``build_container`` testlari — DI to'g'ri ulanishi va uchdan-uchgacha ishlashi."""

from __future__ import annotations

from doda.config import Settings
from doda.container import build_container
from doda.core.models.event import Event


def test_build_container_wires_all_services() -> None:
    container = build_container()
    assert isinstance(container.settings, Settings)
    assert container.events is not None
    assert container.observability is not None
    assert container.secrets is not None
    assert container.flags is not None
    assert container.llm is not None
    assert container.memory is not None
    assert container.tools is not None
    assert container.agent is not None
    assert container.vision is not None
    assert container.environment is not None
    assert container.planning is not None
    assert container.voice is not None
    assert container.realtime_voice is not None
    assert container.scheduler is not None
    assert container.plugins is not None
    assert container.orchestrator is not None
    assert container.daemon is not None
    assert container.evaluation is not None
    assert container.telemetry is not None
    # Agent'ga built-in asboblar ulangan (tool-loop uchun).
    assert len(container.tools.specs()) >= 1


def test_build_container_uses_given_settings() -> None:
    settings = Settings(env="prod")
    container = build_container(settings)
    assert container.settings is settings


async def test_container_event_bus_is_functional() -> None:
    container = build_container()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    container.events.subscribe("x", handler)
    await container.events.publish(Event(name="x"))

    assert len(received) == 1
