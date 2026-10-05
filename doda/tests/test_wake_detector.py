"""``KeywordWakeDetector`` testi — STT+mikrofon asosidagi wake aniqlash."""

from __future__ import annotations

from collections.abc import Sequence

from code.doda.providers.voice import FakeAudioInput, KeywordWakeDetector
from code.doda.tests.contracts.voice_contracts import WakeWordContract


class ScriptedSTT:
    """Har chaqiruvda navbatdagi matnni qaytaradi (oxirgida to'xtaydi)."""

    def __init__(self, transcripts: Sequence[str]) -> None:
        self._transcripts = list(transcripts)
        self._i = 0

    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        text = self._transcripts[min(self._i, len(self._transcripts) - 1)]
        self._i += 1
        return text


class TestKeywordWakeDetector(WakeWordContract):
    def make_wake(self) -> KeywordWakeDetector:
        return KeywordWakeDetector(FakeAudioInput(), ScriptedSTT(["doda"]))


async def test_returns_when_keyword_present() -> None:
    stt = ScriptedSTT(["doda, menga yordam ber"])
    detector = KeywordWakeDetector(FakeAudioInput(), stt)
    await detector.wait_for_wake()  # keyword darhol topiladi


async def test_loops_until_keyword() -> None:
    stt = ScriptedSTT(["shovqin", "boshqa gap", "hey DODA"])
    detector = KeywordWakeDetector(FakeAudioInput(), stt)
    await detector.wait_for_wake()
    assert stt._i == 3  # uchinchi bo'lakda topildi


async def test_custom_keywords() -> None:
    stt = ScriptedSTT(["kompyuter yordam ber"])
    detector = KeywordWakeDetector(FakeAudioInput(), stt, keywords=("kompyuter",))
    await detector.wait_for_wake()
