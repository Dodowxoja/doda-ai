"""``LLMProvider`` porti — AI model provayderi abstraksiyasi (Claude/Gemini/OpenAI/lokal).

Bu **domen porti**: Foundation'da emas, o'z modulida (M2) — birinchi implementatsiya
(``ClaudeProvider``) va contract-test bilan birga — belgilanadi. Agent faqat shu portni
biladi; provayder registry orqali config'dan tanlanadi (vendor-lock yo'q).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from doda.core.models.llm import Capabilities, LLMRequest, LLMResponse, StreamChunk


@runtime_checkable
class LLMProvider(Protocol):
    """AI model provayderi."""

    @property
    def name(self) -> str:
        """Provayder nomi (masalan ``"claude"``)."""
        ...

    @property
    def capabilities(self) -> Capabilities:
        """Provayder qo'llab-quvvatlaydigan imkoniyatlar (streaming/tools/vision)."""
        ...

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """So'rovga to'liq javob qaytaradi (bloklab).

        Raises:
            doda.core.errors.LLMError: Provayder darajasidagi xatoda.
        """
        ...

    def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Javobni bo'lak-bo'lak (stream) qaytaradi (``async for`` bilan o'qiladi)."""
        ...
