"""``EventBridge`` — EventBus'ni WebSocket klientlariga ulaydi (real-time push).

Belgilangan katalogdagi engine-eventlariga obuna bo'ladi, ularni dashboard-eventlariga
tarjima qiladi (``protocol.translate``) va barcha ulangan klient-sinklariga uzatadi. Bir sink
xato bersa, u ro'yxatdan chiqariladi (boshqalari buzilmaydi). Transport-agnostik: sink faqat
``send(str)`` biladi — WebSocket, test yoki boshqa transport bo'lishi mumkin.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from doda.core.interfaces.bus import EventBus, Subscription
from doda.core.interfaces.observability import Observability
from doda.core.models.event import Event
from doda.interfaces.api.protocol import encode, translate

#: Dashboardga uzatiladigan engine-eventlari katalogi (barcha modullardan).
EVENT_CATALOG: tuple[str, ...] = (
    "thinking.step",
    "message.created",
    "tool.called",
    "tool.result",
    "perception.frame",
    "vision.result",
    "perception.env",
    "plan.created",
    "plan.step.started",
    "plan.step.completed",
    "plan.verified",
    "plan.completed",
    "task.scheduled",
    "task.fired",
    "task.completed",
    "task.cancelled",
    "voice.state",
    "voice.wake",
    "voice.transcribed",
    "voice.response",
    "voice.spoken",
    "voice.started",
    "voice.final_transcript",
    "voice.thinking",
    "voice.speaking",
    "voice.interrupted",
    "voice.completed",
    "voice.error",
    "agent.routed",
    "plugin.loaded",
    "plugin.failed",
    "plugin.unloaded",
    "daemon.started",
    "daemon.tick",
    "daemon.tick_error",
    "daemon.stopped",
    "eval.completed",
    "telemetry.snapshot",
    "memory.saved",
)


@runtime_checkable
class ClientSink(Protocol):
    """Klient ulanishi — matn xabar qabul qiladi (WebSocket send)."""

    async def send(self, message: str) -> None:
        """Klientga matn xabar yuboradi."""
        ...


class EventBridge:
    """EventBus eventlarini ulangan klientlarga uzatuvchi ko'prik."""

    def __init__(
        self,
        events: EventBus,
        *,
        catalog: Sequence[str] = EVENT_CATALOG,
        observability: Observability | None = None,
    ) -> None:
        self._events = events
        self._catalog = tuple(catalog)
        self._obs = observability
        self._sinks: set[ClientSink] = set()
        self._subs: list[Subscription] = []

    @property
    def client_count(self) -> int:
        """Ulangan klientlar soni."""
        return len(self._sinks)

    def register(self, sink: ClientSink) -> None:
        """Yangi klientni ro'yxatga qo'shadi."""
        self._sinks.add(sink)

    def unregister(self, sink: ClientSink) -> None:
        """Klientni ro'yxatdan chiqaradi (idempotent)."""
        self._sinks.discard(sink)

    def start(self) -> None:
        """Katalogdagi barcha eventlarga obuna bo'ladi."""
        for name in self._catalog:
            self._subs.append(self._events.subscribe(name, self._on_event))

    def stop(self) -> None:
        """Barcha obunalarni bekor qiladi."""
        for sub in self._subs:
            sub.unsubscribe()
        self._subs.clear()

    async def broadcast(self, event: str, data: Mapping[str, Any]) -> None:
        """Bitta ``{event,data}`` xabarni barcha klientlarga uzatadi."""
        await self._send_raw(encode(event, data))

    async def _on_event(self, event: Event) -> None:
        for message in translate(event):
            await self._send_raw(encode(message["event"], message["data"]))

    async def _send_raw(self, payload: str) -> None:
        dead: list[ClientSink] = []
        for sink in tuple(self._sinks):
            try:
                await sink.send(payload)
            except Exception as exc:  # o'lik ulanish — ro'yxatdan chiqaramiz
                dead.append(sink)
                if self._obs is not None:
                    self._obs.log("debug", "klient sink xato berdi", error=repr(exc))
        for sink in dead:
            self._sinks.discard(sink)
