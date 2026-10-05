"""``KeywordRouter`` — kalit-so'z asosida so'rovni agentga yo'naltiradi.

Oddiy, deterministik va tez (LLM'siz). Kelajakda LLM-asosli router shu port ortida
almashtirilishi mumkin (Orchestrator o'zgarmaydi).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

_DEFAULT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "coding": ("kod", "code", "dastur", "python", "bug", "xato tuzat"),
    "vision": ("rasm", "ko'r", "ekran", "surat", "kamera"),
    "research": ("qidir", "izla", "malumot top", "research", "tadqiq"),
}


class KeywordRouter:
    """Matndagi kalit-so'zga qarab agent nomini tanlaydi; topilmasa ``default``."""

    def __init__(
        self,
        keywords: Mapping[str, Sequence[str]] | None = None,
        *,
        default: str = "main",
    ) -> None:
        source = keywords if keywords is not None else _DEFAULT_KEYWORDS
        self._keywords = {agent: tuple(words) for agent, words in source.items()}
        self._default = default

    async def route(self, text: str) -> str:
        lowered = text.lower()
        for agent, words in self._keywords.items():
            if any(word in lowered for word in words):
                return agent
        return self._default
