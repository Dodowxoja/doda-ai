"""``AsyncioEventBus`` — EventBus portining lokal asyncio implementatsiyasi.

Ataylab **oddiy** (ADR-005): aniq-nomli obuna, ``asyncio`` bilan yetkazish. Wildcard,
prioritet yoki tashqi broker YO'Q — kelajakda kerak bo'lsa shu port ortida qo'shiladi.

**Xato izolyatsiyasi:** bir handler xato bersa, boshqalari baribir ishlaydi; xato
Observability'ga loglanadi (nashr etuvchi buzilmaydi).
"""

from __future__ import annotations

import asyncio
from typing import Any

from doda.core.interfaces.bus import EventHandler
from doda.core.interfaces.observability import Observability
from doda.core.models.event import Event


class _Subscription:
    """:class:`AsyncioEventBus` uchun obuna tutqichi (idempotent unsubscribe)."""

    def __init__(self, bus: AsyncioEventBus, name: str, handler: EventHandler) -> None:
        self._bus = bus
        self._name = name
        self._handler: EventHandler | None = handler

    def unsubscribe(self) -> None:
        """Obunani bekor qiladi. Bir necha marta chaqirish xavfsiz (idempotent)."""
        if self._handler is not None:
            self._bus._remove(self._name, self._handler)
            self._handler = None


class AsyncioEventBus:
    """Lokal, jarayon-ichi pub/sub avtobusi."""

    def __init__(self, observability: Observability | None = None) -> None:
        """
        Args:
            observability: Handler xatolarini loglash uchun (ixtiyoriy).
        """
        self._handlers: dict[str, list[EventHandler]] = {}
        self._obs = observability

    def subscribe(self, name: str, handler: EventHandler) -> _Subscription:
        """``name`` hodisasiga ``handler``ni obuna qiladi."""
        self._handlers.setdefault(name, []).append(handler)
        return _Subscription(self, name, handler)

    async def publish(self, event: Event) -> None:
        """Hodisani obunachilarga parallel yetkazadi (xatolar izolyatsiyalangan)."""
        handlers = list(self._handlers.get(event.name, ()))
        if not handlers:
            return
        results: list[Any] = await asyncio.gather(
            *(handler(event) for handler in handlers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, BaseException):
                self._on_handler_error(event, result)

    def _remove(self, name: str, handler: EventHandler) -> None:
        """Handlerni ro'yxatdan olib tashlaydi (mavjud bo'lsa)."""
        handlers = self._handlers.get(name)
        if handlers is not None and handler in handlers:
            handlers.remove(handler)
            if not handlers:
                del self._handlers[name]

    def _on_handler_error(self, event: Event, error: BaseException) -> None:
        """Handler xatosini loglaydi (nashr etuvchini buzmasdan)."""
        if self._obs is not None:
            self._obs.log(
                "error",
                f"event handler failed for '{event.name}'",
                error=repr(error),
                trace_id=event.trace_id,
            )
