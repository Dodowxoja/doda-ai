"""Audio portlarining soxta implementatsiyalari (mock mode / test uchun)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from doda.core.models.speech import SpeechChunk


class FakeAudioInput:
    """Belgilangan audio-baytlarni "yozib beradigan" soxta mikrofon."""

    def __init__(self, audio: bytes = b"AUDIO") -> None:
        self._audio = audio

    async def record(self, *, seconds: float = 5.0) -> bytes:
        return self._audio


class FakeAudioOutput:
    """Ijro etilgan audioni yozib boradigan soxta karnay."""

    def __init__(self) -> None:
        self.played: list[bytes] = []

    async def play(self, audio: bytes) -> None:
        self.played.append(audio)


class FakeStreamingAudioInput:
    """Belgilangan kadrlar oqimini beradigan soxta streaming mikrofon."""

    def __init__(self, frames: Sequence[bytes] = (b"f1", b"f2")) -> None:
        self._frames = list(frames)

    async def stream(self, *, frame_ms: int = 30) -> AsyncIterator[SpeechChunk]:
        for i, frame in enumerate(self._frames):
            yield SpeechChunk(audio=frame, is_last=i == len(self._frames) - 1)
