"""``EventBus`` porti uchun contract — har qanday implementatsiya bajarishi shart.

Yangi EventBus (masalan kelajakdagi Redis/NATS) shu klassni meros olib ``make_bus()``ni
belgilaydi — barcha kelishuv testlari avtomatik ishlaydi.
"""

from __future__ import annotations

from doda.core.interfaces.bus import EventBus
from doda.core.models.event import Event


class EventBusContract:
    """EventBus kelishuvi (subklass ``make_bus()``ni beradi)."""

    def make_bus(self) -> EventBus:
        """Test qilinadigan yangi (bo'sh) EventBus qaytaradi."""
        raise NotImplementedError

    async def test_delivers_to_subscriber(self) -> None:
        bus = self.make_bus()
        received: list[Event] = []

        async def handler(event: Event) -> None:
            received.append(event)

        bus.subscribe("ping", handler)
        event = Event(name="ping", payload={"x": 1})
        await bus.publish(event)

        assert received == [event]

    async def test_only_matching_name_delivered(self) -> None:
        bus = self.make_bus()
        got: list[str] = []

        async def handler(event: Event) -> None:
            got.append(event.name)

        bus.subscribe("a", handler)
        await bus.publish(Event(name="b"))

        assert got == []

    async def test_multiple_handlers_all_receive(self) -> None:
        bus = self.make_bus()
        calls: list[str] = []

        async def h1(event: Event) -> None:
            calls.append("h1")

        async def h2(event: Event) -> None:
            calls.append("h2")

        bus.subscribe("e", h1)
        bus.subscribe("e", h2)
        await bus.publish(Event(name="e"))

        assert sorted(calls) == ["h1", "h2"]

    async def test_unsubscribe_stops_delivery(self) -> None:
        bus = self.make_bus()
        count = 0

        async def handler(event: Event) -> None:
            nonlocal count
            count += 1

        subscription = bus.subscribe("e", handler)
        await bus.publish(Event(name="e"))
        subscription.unsubscribe()
        await bus.publish(Event(name="e"))

        assert count == 1

    async def test_unsubscribe_is_idempotent(self) -> None:
        bus = self.make_bus()

        async def handler(event: Event) -> None:
            return None

        subscription = bus.subscribe("e", handler)
        subscription.unsubscribe()
        subscription.unsubscribe()  # ikkinchi marta xato bermasligi kerak

    async def test_publish_without_subscribers_is_ok(self) -> None:
        bus = self.make_bus()
        await bus.publish(Event(name="nobody-listens"))

    async def test_handler_error_is_isolated(self) -> None:
        bus = self.make_bus()
        good_ran = False

        async def bad(event: Event) -> None:
            raise RuntimeError("boom")

        async def good(event: Event) -> None:
            nonlocal good_ran
            good_ran = True

        bus.subscribe("e", bad)
        bus.subscribe("e", good)
        await bus.publish(Event(name="e"))

        assert good_ran is True
