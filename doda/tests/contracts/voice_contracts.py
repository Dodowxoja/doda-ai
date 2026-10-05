"""Ovoz portlari uchun contract-test bazalari (STT/TTS/AudioInput/AudioOutput/WakeWord)."""

from __future__ import annotations

from doda.core.interfaces.voice import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
    VoiceActivityDetector,
    WakeWordDetector,
)


class STTContract:
    """Har bir ``SpeechToText`` transkript (matn) qaytarishi shart."""

    def make_stt(self) -> SpeechToText:
        raise NotImplementedError

    async def test_transcribe_returns_str(self) -> None:
        result = await self.make_stt().transcribe(b"AUDIO")
        assert isinstance(result, str)


class TTSContract:
    """Har bir ``TextToSpeech`` audio (baytlar) qaytarishi shart."""

    def make_tts(self) -> TextToSpeech:
        raise NotImplementedError

    async def test_synthesize_returns_bytes(self) -> None:
        result = await self.make_tts().synthesize("salom")
        assert isinstance(result, bytes)


class AudioInputContract:
    """Har bir ``AudioInput`` audio (baytlar) yozib berishi shart."""

    def make_audio_input(self) -> AudioInput:
        raise NotImplementedError

    async def test_record_returns_bytes(self) -> None:
        result = await self.make_audio_input().record(seconds=1.0)
        assert isinstance(result, bytes)


class AudioOutputContract:
    """Har bir ``AudioOutput`` audio baytlarini qabul qilib ijro etishi shart."""

    def make_audio_output(self) -> AudioOutput:
        raise NotImplementedError

    async def test_play_accepts_bytes(self) -> None:
        await self.make_audio_output().play(b"AUDIO")


class WakeWordContract:
    """Har bir ``WakeWordDetector`` aniqlanganda ``wait_for_wake`` dan qaytishi shart."""

    def make_wake(self) -> WakeWordDetector:
        raise NotImplementedError

    async def test_wait_for_wake_completes(self) -> None:
        await self.make_wake().wait_for_wake()


class VADContract:
    """Har bir ``VoiceActivityDetector`` bool qaytarishi va ``reset`` ni qo'llashi shart."""

    def make_vad(self) -> VoiceActivityDetector:
        raise NotImplementedError

    async def test_is_speech_returns_bool(self) -> None:
        result = await self.make_vad().is_speech(b"\x00\x00" * 80)
        assert isinstance(result, bool)

    def test_reset_is_callable(self) -> None:
        self.make_vad().reset()
