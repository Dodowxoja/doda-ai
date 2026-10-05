"""``Event`` — Event Bus orqali tarqaladigan domen hodisasi.

Hodisa **o'zgarmas** (immutable, ``frozen``) — bir marta yaratilgach o'zgarmaydi, shuning
uchun uni ko'p obunachiga xavfsiz uzatib bo'ladi. ``trace_id`` butun kognitiv tsiklni
uchdan-uchgacha kuzatishga xizmat qiladi (Observability).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _new_trace_id() -> str:
    """Yangi noyob trace identifikatori (hex UUID)."""
    return uuid4().hex


def _now() -> datetime:
    """Joriy UTC vaqti."""
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Event:
    """Tizimda sodir bo'lgan bitta hodisa.

    Attributes:
        name: Hodisa nomi, nuqta bilan bo'limlangan (masalan ``"message.created"``).
            Obunachi shu nom bo'yicha tinglaydi.
        payload: Hodisaga oid ma'lumot (o'zgarmas ko'rinishda, JSON-mos bo'lishi kutiladi).
        trace_id: So'rovni uchdan-uchgacha bog'lash uchun identifikator.
        source: Hodisani chiqargan modul/komponent nomi (masalan ``"agent"``).
        timestamp: Hodisa yaratilgan UTC vaqti.
    """

    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=_new_trace_id)
    source: str = ""
    timestamp: datetime = field(default_factory=_now)
