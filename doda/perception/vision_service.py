"""``VisionService`` — "Nima ko'ryapsan?" oqimi (kadr → LLM Vision → tasvir).

Kameradan kadr oladi, uni fikrlash vositasiga (LLM, vision-qobiliyatli) yuboradi va matnli
tasvirni qaytaradi. Har qadam ``perception.*`` / ``vision.*`` eventi (Brain Studio uchun).
Faqat portlarga tayanadi (VisionProvider, LLMProvider, EventBus).
"""

from __future__ import annotations

import base64
from collections.abc import Mapping
from typing import Any

from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.llm import LLMProvider
from doda.core.interfaces.observability import Observability
from doda.core.interfaces.perception import VisionProvider
from doda.core.models.event import Event
from doda.core.models.llm import ImageContent, LLMRequest, Message, Role, TextContent

_DEFAULT_QUESTION = "Nima ko'ryapsan? Qisqa tasvirlab ber."
_SOURCE = "vision"


class VisionService:
    """Kadr olib LLM Vision orqali tasvirlaydigan servis."""

    def __init__(
        self,
        *,
        vision: VisionProvider,
        llm: LLMProvider,
        events: EventBus,
        observability: Observability | None = None,
    ) -> None:
        self._vision = vision
        self._llm = llm
        self._events = events
        self._obs = observability

    async def describe(self, question: str = _DEFAULT_QUESTION) -> str:
        """Joriy kadrni olib, ``question`` bo'yicha tasvirni qaytaradi."""
        frame = await self._vision.capture()
        await self._emit(
            "perception.frame", {"source": frame.source, "media_type": frame.media_type}
        )
        image = ImageContent(
            media_type=frame.media_type,
            data=base64.b64encode(frame.data).decode("ascii"),
        )
        message = Message(role=Role.USER, content=(image, TextContent(question)))
        response = await self._llm.chat(LLMRequest(messages=(message,)))
        await self._emit("vision.result", {"result": response.text})
        return response.text

    async def _emit(self, name: str, payload: Mapping[str, Any]) -> None:
        await self._events.publish(Event(name=name, payload=payload, source=_SOURCE))
