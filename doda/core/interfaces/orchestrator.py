"""``AgentRouter`` porti — so'rovni mos agentga yo'naltirish (Multi-Agent).

``Orchestrator`` (M11) so'rovni tegishli agentga (Main/Coding/Vision/Research...) uzatadi.
v1.0 da bitta ``CognitiveAgent`` bor, ammo interfeys tayyor — yangi agent shunchaki ro'yxatga
qo'shiladi (yadro o'zgarmaydi). Router kalit-so'z yoki LLM asosida ishlashi mumkin (async).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AgentRouter(Protocol):
    """So'rov matniga qarab qaysi agent ishlashi kerakligini tanlaydi."""

    async def route(self, text: str) -> str:
        """So'rov uchun agent nomini qaytaradi (masalan "coding" / "vision" / "main")."""
        ...
