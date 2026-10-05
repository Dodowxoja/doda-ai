"""Xotira (Memory) domen modellari — o'zgarmas.

7 qatlamli xotiraning **doimiy** qatlamlari shu modellar bilan ifodalanadi (Working va
Conversation qatlamlari vaqtinchalik — agent holatida). ``type`` qaysi qatlamga tegishlini
ko'rsatadi. Qarang: ``doda/ARCHITECTURE.md`` §5, ``docs/DATABASE.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


class MemoryType(StrEnum):
    """Xotira turi (7-qatlam modeliga xaritalanadi)."""

    FACT = "fact"  # Semantic: fakt/tushuncha
    EPISODIC = "episodic"  # Episodic: qachon/nima bo'ldi
    PREFERENCE = "preference"  # User Profile: afzallik/uslub
    PROJECT = "project"  # Long-term
    PLAN = "plan"  # Long-term
    HABIT = "habit"  # Long-term
    INTEREST = "interest"  # Long-term
    SUMMARY = "summary"  # Conversation xulosasi
    KNOWLEDGE = "knowledge"  # Knowledge Base (RAG)


def _now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class MemoryItem:
    """Bitta xotira yozuvi (fakt/voqea/afzallik/…)."""

    id: str
    content: str
    type: MemoryType
    user_id: str = "owner"
    importance: float = 0.5
    source: str = ""
    created_at: datetime = field(default_factory=_now)
    valid: bool = True

    @classmethod
    def create(
        cls,
        content: str,
        type: MemoryType,
        *,
        user_id: str = "owner",
        importance: float = 0.5,
        source: str = "",
    ) -> MemoryItem:
        """Yangi ID bilan xotira yozuvi yaratadi."""
        return cls(
            id=uuid4().hex,
            content=content,
            type=type,
            user_id=user_id,
            importance=importance,
            source=source,
        )
