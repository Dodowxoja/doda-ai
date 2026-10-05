"""Ovoz provayderlari testlari — soxta FileRunner bilan buyruq/natija tekshiruvi."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from code.doda.core.interfaces.voice import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
)
from code.doda.providers.voice import (
    AfplayOutput,
    EdgeTTS,
    FakeAudioInput,
    FakeAudioOutput,
    FakeSTT,
    FakeTTS,
    FfmpegRecorder,
    WhisperSTT,
)
from code.doda.tests.contracts.voice_contracts import (
    AudioInputContract,
    AudioOutputContract,
    STTContract,
    TTSContract,
)


def file_runner(
    *,
    writes_bytes: bytes | None = None,
    writes_text: str | None = None,
    capture: dict[str, Any] | None = None,
) -> Any:
    async def runner(command: Sequence[str], output_path: Path) -> None:
        if capture is not None:
            capture["command"] = list(command)
        if writes_bytes is not None:
            output_path.write_bytes(writes_bytes)
        if writes_text is not None:
            output_path.write_text(writes_text, "utf-8")

    return runner


# ---------------- Fakes ----------------


class TestFakeSTT(STTContract):
    def make_stt(self) -> SpeechToText:
        return FakeSTT()


class TestFakeTTS(TTSContract):
    def make_tts(self) -> TextToSpeech:
        return FakeTTS()


class TestFakeAudioInput(AudioInputContract):
    def make_audio_input(self) -> AudioInput:
        return FakeAudioInput()


class TestFakeAudioOutput(AudioOutputContract):
    def make_audio_output(self) -> AudioOutput:
        return FakeAudioOutput()


# ---------------- EdgeTTS ----------------


class TestEdgeTTS(TTSContract):
    def make_tts(self) -> TextToSpeech:
        return EdgeTTS(runner=file_runner(writes_bytes=b"MP3"))

    async def test_uses_edge_tts_with_voice_and_text(self) -> None:
        captured: dict[str, Any] = {}
        tts = EdgeTTS(
            voice="uz-UZ-MadinaNeural", runner=file_runner(writes_bytes=b"MP3", capture=captured)
        )
        result = await tts.synthesize("assalom")
        assert result == b"MP3"
        assert captured["command"][0] == "edge-tts"
        assert "uz-UZ-MadinaNeural" in captured["command"]
        assert "assalom" in captured["command"]


# ---------------- WhisperSTT ----------------


class TestWhisperSTT(STTContract):
    def make_stt(self) -> SpeechToText:
        return WhisperSTT(runner=file_runner(writes_text="natija"))

    async def test_transcribes_and_strips(self) -> None:
        captured: dict[str, Any] = {}
        stt = WhisperSTT(runner=file_runner(writes_text="  salom dunyo \n", capture=captured))
        result = await stt.transcribe(b"AUDIO", language="uz")
        assert result == "salom dunyo"
        assert captured["command"][0] == "whisper"
        assert "uz" in captured["command"]


# ---------------- FfmpegRecorder ----------------


class TestFfmpegRecorder(AudioInputContract):
    def make_audio_input(self) -> AudioInput:
        return FfmpegRecorder(runner=file_runner(writes_bytes=b"WAV"))

    async def test_records_via_ffmpeg(self) -> None:
        captured: dict[str, Any] = {}
        recorder = FfmpegRecorder(runner=file_runner(writes_bytes=b"WAV", capture=captured))
        result = await recorder.record(seconds=3.0)
        assert result == b"WAV"
        assert captured["command"][0] == "ffmpeg"
        assert "avfoundation" in captured["command"]
        assert "3.0" in captured["command"]


# ---------------- AfplayOutput ----------------


class TestAfplayOutput(AudioOutputContract):
    def make_audio_output(self) -> AudioOutput:
        return AfplayOutput(runner=file_runner())

    async def test_plays_via_afplay(self) -> None:
        captured: dict[str, Any] = {}
        output = AfplayOutput(runner=file_runner(capture=captured))
        await output.play(b"AUDIO")
        assert captured["command"][0] == "afplay"
