"""Soxta STT (mock mode / test uchun) — bir martalik + streaming."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from doda.core.models.speech import SpeechResult


class FakeSTT:
    """Sozlangan matnni qaytaradigan STT; kirish audiosini yozib boradi."""

    def __init__(self, transcript: str = "salom") -> None:
        self._transcript = transcript
        self.calls: list[bytes] = []

    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        self.calls.append(audio)
        return self._transcript


class FakeStreamingSTT:
    """Qisman → yakuniy transkriptlar oqimini beradigan soxta streaming STT."""

    def __init__(self, partials: Sequence[str] = ("salom",), final: str = "salom doda") -> None:
        self._partials = list(partials)
        self._final = final

    async def transcribe_stream(
        self, audio: AsyncIterator[bytes], *, language: str = "uz"
    ) -> AsyncIterator[SpeechResult]:
        async for _ in audio:
            pass
        for partial in self._partials:
            yield SpeechResult(text=partial, is_final=False, language=language)
        yield SpeechResult(text=self._final, is_final=True, language=language)
