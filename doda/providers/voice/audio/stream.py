"""``FrameStreamAdapter`` — bir martalik ``AudioInput``ni oqimga (``StreamingAudioInput``) o'raydi.

Kutubxonasiz streaming yo'li: mavjud rekorderni qisqa kadrlarga bo'lib takror yozadi. Bu
``sounddevice``/``pyaudio``siz ishlaydi va to'liq test qilinadi. Haqiqiy past-kechikishli
oqim (bo'lakma-bo'lak mikrofon) kelajakda shu port ortida almashtirilishi mumkin.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from code.doda.core.interfaces.voice import AudioInput
from code.doda.core.models.speech import SpeechChunk


class FrameStreamAdapter:
    """Bir martalik ``AudioInput``ni kadrlar oqimiga aylantiradi."""

    def __init__(
        self, audio: AudioInput, *, frame_seconds: float = 0.5, max_frames: int | None = None
    ) -> None:
        """Adapterni quradi.

        Args:
            audio: O'ralayotgan bir martalik mikrofon.
            frame_seconds: Har bir kadr uzunligi (soniya).
            max_frames: Test/chegara uchun — shu miqdordan keyin oqim tugaydi (None = cheksiz).
        """
        self._audio = audio
        self._frame_seconds = frame_seconds
        self._max_frames = max_frames

    async def stream(self, *, frame_ms: int = 30) -> AsyncIterator[SpeechChunk]:
        """Mikrofondan audio kadrlar oqimini beradi (``frame_ms`` — maslahat, aniq emas)."""
        count = 0
        while self._max_frames is None or count < self._max_frames:
            data = await self._audio.record(seconds=self._frame_seconds)
            count += 1
            is_last = self._max_frames is not None and count >= self._max_frames
            yield SpeechChunk(audio=data, is_last=is_last)
