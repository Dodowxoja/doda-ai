"""``Agent`` va ``ToolExecutor`` portlari.

``Agent`` — foydalanuvchi so'roviga javob beruvchi kognitiv birlik. Multi-Agent (M11) da
``Orchestrator`` so'rovni mos ``Agent``ga yo'naltiradi (hozir bitta ``CognitiveAgent``).

``ToolExecutor`` — Agent tomonidan chaqirilgan asbobni bajaruvchi. Konkret asboblar va ularning
registri M6 (Tools) da; Agent faqat shu tor kelishuvni biladi (asbobni bajar → natija).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from doda.core.models.llm import ToolCall


@runtime_checkable
class ToolExecutor(Protocol):
    """Asbob-chaqiruvni bajarib, natija matnini qaytaradi."""

    async def execute(self, call: ToolCall) -> str:
        """``call`` asbobini bajaradi va natijani (matn) qaytaradi."""
        ...


@runtime_checkable
class Agent(Protocol):
    """Foydalanuvchi so'roviga javob beruvchi kognitiv agent."""

    async def handle(self, user_text: str) -> str:
        """Foydalanuvchi matniga javob qaytaradi (kognitiv tsikl orqali)."""
        ...


@runtime_checkable
class StreamingAgent(Protocol):
    """Javobni bo'lak-bo'lak (stream) qaytara oladigan agent.

    ``handle``dan farqi: javob to'liq kutilmasdan, matn bo'laklari (delta) ketma-ket keladi —
    real-time UI (dashboard chunk) uchun. Asboblar (tool-loop) stream rejimida ishlatilmaydi;
    murakkab asbobli so'rovlar uchun ``Agent.handle`` ishlatiladi.
    """

    def stream(self, user_text: str) -> AsyncIterator[str]:
        """Javob matnini bo'laklar (delta) oqimi sifatida qaytaradi."""
        ...
