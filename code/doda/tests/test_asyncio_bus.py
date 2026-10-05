"""``AsyncioEventBus`` testlari — EventBus contract + implementatsiya-xususiy xatti-harakat."""

from __future__ import annotations

import pytest

from code.doda.core.interfaces.bus import EventBus
from code.doda.core.models.event import Event
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.observability import BasicObservability
from code.doda.tests.contracts.event_bus_contract import EventBusContract


class TestAsyncioEventBus(EventBusContract):
    """AsyncioEventBus EventBus kelishuvini bajaradi + o'ziga xos testlar."""

    def make_bus(self) -> EventBus:
        return AsyncioEventBus()

    async def test_handler_error_is_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        observability = BasicObservability()
        bus = AsyncioEventBus(observability=observability)

        async def bad(event: Event) -> None:
            raise RuntimeError("boom")

        bus.subscribe("e", bad)
        with caplog.at_level("ERROR", logger="doda"):
            await bus.publish(Event(name="e"))

        assert any("event handler failed" in record.getMessage() for record in caplog.records)
