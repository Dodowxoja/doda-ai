"""``KeywordWakeDetector`` — STT-asosli wake-so'z detektori (kutubxonasiz).

Qisqa audio bo'laklarini yozib (``AudioInput``), STT bilan transkripsiya qiladi va wake-so'z
("doda") uchraganini tekshiradi. Maxsus wake-engine (openWakeWord/porcupine) v1.1 ga qoldirildi;
bu implementatsiya mavjud STT+mikrofonni qayta ishlatadi (to'liq test qilinadi).
"""

from __future__ import annotations

from collections.abc import Sequence

from code.doda.core.interfaces.voice import AudioInput, SpeechToText


class KeywordWakeDetector:
    """Qisqa bo'laklarni tinglab, wake-so'z uchraguncha kutadi."""

    def __init__(
        self,
        audio: AudioInput,
        stt: SpeechToText,
        *,
        keywords: Sequence[str] = ("doda",),
        chunk_seconds: float = 2.0,
    ) -> None:
        self._audio = audio
        self._stt = stt
        self._keywords = tuple(k.lower() for k in keywords)
        self._chunk_seconds = chunk_seconds

    async def wait_for_wake(self) -> None:
        """Wake-so'z aniqlanmaguncha qisqa bo'laklarni tinglaydi."""
        while True:
            clip = await self._audio.record(seconds=self._chunk_seconds)
            text = (await self._stt.transcribe(clip)).lower()
            if any(keyword in text for keyword in self._keywords):
                return
