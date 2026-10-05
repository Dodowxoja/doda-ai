"""``EventBus`` porti — modullararo pub/sub abstraksiyasi (core, implementatsiyasiz).

Nashr etuvchi (publisher) obunachilarni (subscribers) BILMAYDI — faqat hodisa nomini
biladi. Bu modullarni bir-biridan ajratadi (Open/Closed): yangi modul/plugin shunchaki
obuna bo'ladi, mavjud kodni o'zgartirmasdan.

Implementatsiya ``providers/bus/`` da (hozir lokal asyncio; kelajakda NATS/Redis).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from doda.core.models.event import Event

EventHandler = Callable[[Event], Awaitable[None]]
"""Hodisani qabul qiladigan asinxron funksiya turi."""


@runtime_checkable
class Subscription(Protocol):
    """Obunani boshqarish uchun tutqich (subscribe() qaytaradi)."""

    def unsubscribe(self) -> None:
        """Obunani bekor qiladi — handler boshqa hodisa olmaydi. Idempotent."""
        ...


@runtime_checkable
class EventBus(Protocol):
    """Modullararo hodisa avtobusi (pub/sub)."""

    async def publish(self, event: Event) -> None:
        """``event``ni shu nomga obuna bo'lgan barcha handlerlarga yetkazadi.

        Handlerlardan biri xato bersa, boshqalari baribir ishlaydi (izolyatsiya).
        """
        ...

    def subscribe(self, name: str, handler: EventHandler) -> Subscription:
        """``name`` nomli hodisaga ``handler``ni obuna qiladi.

        Args:
            name: Tinglanadigan hodisa nomi (aniq moslik).
            handler: Hodisa kelganda chaqiriladigan asinxron funksiya.

        Returns:
            Obunani keyin bekor qilish uchun :class:`Subscription`.
        """
        ...
