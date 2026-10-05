"""Ovoz portlari — STT / TTS / WakeWord / mikrofon / karnay.

Ovoz quvuri (M8) shu portlarni birlashtiradi: wake-so'z → mikrofon → STT → Agent → TTS →
karnay. Konkret (subprocess/hardware) implementatsiyalar ``doda/providers/voice/`` da;
har biri DI orqali almashtiriladi (test uchun soxta variantlar).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from doda.core.models.speech import SpeechChunk, SpeechResult


@runtime_checkable
class SpeechToText(Protocol):
    """Ovoz (audio baytlari) → matn (bir martalik)."""

    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        """Audio'ni ``language`` tilida matnga aylantiradi."""
        ...


@runtime_checkable
class StreamingSpeechToText(Protocol):
    """Real-vaqt STT — audio oqimidan qisman/yakuniy transkriptlar beradi."""

    def transcribe_stream(
        self, audio: AsyncIterator[bytes], *, language: str = "uz"
    ) -> AsyncIterator[SpeechResult]:
        """Audio oqimini transkript oqimiga aylantiradi (partial→final)."""
        ...


@runtime_checkable
class VoiceActivityDetector(Protocol):
    """Ovoz-faollik aniqlash (VAD) — kadrda nutq bor-yo'qligini aytadi."""

    async def is_speech(self, frame: bytes) -> bool:
        """``frame`` (audio bo'lagi) nutq o'z ichiga oladimi."""
        ...

    def reset(self) -> None:
        """Detektorning ichki holatini tozalaydi (yangi sessiya uchun)."""
        ...


@runtime_checkable
class TextToSpeech(Protocol):
    """Matn → ovoz (audio baytlari)."""

    async def synthesize(self, text: str) -> bytes:
        """Matndan audio (baytlar) yaratadi."""
        ...


@runtime_checkable
class AudioInput(Protocol):
    """Mikrofon — audio yozib oladi (bir martalik)."""

    async def record(self, *, seconds: float = 5.0) -> bytes:
        """``seconds`` davomida audio yozib, baytlar qaytaradi."""
        ...


@runtime_checkable
class StreamingAudioInput(Protocol):
    """Mikrofon — audioni uzluksiz bo'laklar oqimi sifatida beradi (VAD/realtime uchun)."""

    def stream(self, *, frame_ms: int = 30) -> AsyncIterator[SpeechChunk]:
        """Mikrofondan ``frame_ms`` uzunlikdagi audio bo'laklar oqimini qaytaradi."""
        ...


@runtime_checkable
class AudioOutput(Protocol):
    """Karnay — audioni ijro etadi."""

    async def play(self, audio: bytes) -> None:
        """Audio baytlarini ijro etadi."""
        ...


@runtime_checkable
class WakeWordDetector(Protocol):
    """Wake-so'z ("DODA") kutuvchi."""

    async def wait_for_wake(self) -> None:
        """Wake-so'z aniqlanmaguncha kutadi (aniqlanganda qaytadi)."""
        ...
