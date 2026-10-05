"""``EnvironmentService`` testlari — snapshot + event + sensor izolyatsiyasi."""

from __future__ import annotations

import logging

import pytest

from code.doda.core.models.event import Event
from code.doda.perception import EnvironmentService
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.env import FakeEnvSensor
from code.doda.providers.observability import BasicObservability


async def test_snapshot_aggregates_sensors() -> None:
    service = EnvironmentService(
        [FakeEnvSensor(name="a", value="1"), FakeEnvSensor(name="b", value="2")],
        AsyncioEventBus(),
    )
    assert await service.snapshot() == {"a": "1", "b": "2"}


async def test_emits_env_event() -> None:
    events = AsyncioEventBus()
    seen: list[dict[str, str]] = []

    async def on_event(event: Event) -> None:
        seen.append(dict(event.payload["snapshot"]))

    events.subscribe("perception.env", on_event)
    service = EnvironmentService([FakeEnvSensor(name="a", value="1")], events)

    await service.snapshot()
    assert seen[0] == {"a": "1"}


async def test_failing_sensor_is_isolated() -> None:
    service = EnvironmentService(
        [FakeEnvSensor(name="bad", fail=True), FakeEnvSensor(name="ok", value="v")],
        AsyncioEventBus(),
    )
    snapshot = await service.snapshot()
    assert snapshot["ok"] == "v"
    assert "xato" in snapshot["bad"]


async def test_failing_sensor_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("doda.test.env")
    service = EnvironmentService(
        [FakeEnvSensor(name="bad", fail=True)],
        AsyncioEventBus(),
        observability=BasicObservability(logger=logger),
    )
    with caplog.at_level(logging.WARNING, logger="doda.test.env"):
        await service.snapshot()
    assert any("bad" in record.message for record in caplog.records)
