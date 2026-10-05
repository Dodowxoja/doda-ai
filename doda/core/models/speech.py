"""Ovoz domen modellari — ``VoiceState`` / ``SpeechResult`` / ``SpeechChunk`` / ``SpeechConfig``.

Ovoz quvuri va sessiya holat-mashinasi shu modellar bilan ishlaydi. Streaming STT qisman
(``is_final=False``) va yakuniy (``is_final=True``) natijalarni ``SpeechResult`` orqali ajratadi.
Modellar o'zgarmas (frozen) — sof domen, tashqi kutubxonaga bog'liq emas.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VoiceState(StrEnum):
    """Ovoz sessiyasining holat-mashinasi holatlari."""

    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class SpeechChunk:
    """Audio oqimining bir bo'lagi (mikrofondan / TTS'dan)."""

    audio: bytes
    is_last: bool = False


@dataclass(frozen=True, slots=True)
class SpeechResult:
    """STT natijasi — qisman yoki yakuniy transkript."""

    text: str
    is_final: bool = True
    confidence: float = 1.0
    language: str = "uz"


@dataclass(frozen=True, slots=True)
class SpeechConfig:
    """Ovoz quvuri sozlamalari (til, namuna chastotasi, streaming)."""

    language: str = "uz"
    sample_rate: int = 16000
    streaming: bool = True
    record_seconds: float = 5.0


@dataclass(frozen=True, slots=True)
class VoiceEvent:
    """Sessiya holati o'zgarishi (kuzatuv/UI uchun)."""

    state: VoiceState
    detail: str = ""
