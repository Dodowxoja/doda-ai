"""Ovoz domen modellari testi — VoiceState / SpeechChunk / SpeechResult / SpeechConfig."""

from __future__ import annotations

import dataclasses

import pytest

from doda.core.models.speech import (
    SpeechChunk,
    SpeechConfig,
    SpeechResult,
    VoiceEvent,
    VoiceState,
)


def test_voice_states() -> None:
    assert VoiceState.IDLE.value == "idle"
    assert VoiceState.SPEAKING.value == "speaking"


def test_speech_chunk_defaults() -> None:
    chunk = SpeechChunk(audio=b"x")
    assert chunk.audio == b"x"
    assert chunk.is_last is False


def test_speech_result_defaults() -> None:
    result = SpeechResult(text="salom")
    assert result.is_final is True
    assert result.confidence == 1.0
    assert result.language == "uz"


def test_speech_config_defaults() -> None:
    cfg = SpeechConfig()
    assert cfg.language == "uz"
    assert cfg.sample_rate == 16000
    assert cfg.streaming is True


def test_voice_event() -> None:
    event = VoiceEvent(state=VoiceState.LISTENING, detail="boshlandi")
    assert event.state == VoiceState.LISTENING
    assert event.detail == "boshlandi"


def test_models_frozen() -> None:
    result = SpeechResult(text="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.text = "y"  # type: ignore[misc]
