"""STT provayderlari — Whisper (default) + ElevenLabs (ixtiyoriy) + soxta."""

from doda.providers.voice.stt.elevenlabs import ElevenLabsSTT
from doda.providers.voice.stt.fake import FakeStreamingSTT, FakeSTT
from doda.providers.voice.stt.whisper import WhisperSTT

__all__ = ["ElevenLabsSTT", "FakeSTT", "FakeStreamingSTT", "WhisperSTT"]
