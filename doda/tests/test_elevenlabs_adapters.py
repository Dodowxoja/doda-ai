"""ElevenLabs STT/TTS adapterlari testi — kalit/kutubxona guardlari (real API'siz)."""

from __future__ import annotations

import pytest

from doda.core.errors import STTError, TTSError
from doda.providers.voice.stt import ElevenLabsSTT
from doda.providers.voice.tts import ElevenLabsTTS


async def test_stt_without_key_raises() -> None:
    with pytest.raises(STTError, match="kalit"):
        await ElevenLabsSTT("").transcribe(b"AUDIO")


async def test_stt_without_library_raises() -> None:
    # elevenlabs kutubxonasi o'rnatilmagan → aniq STTError (crash emas).
    with pytest.raises(STTError, match="o'rnatilmagan"):
        await ElevenLabsSTT("fake-key").transcribe(b"AUDIO")


async def test_tts_without_key_raises() -> None:
    with pytest.raises(TTSError, match="kalit"):
        await ElevenLabsTTS("", voice_id="v1").synthesize("salom")


async def test_tts_without_voice_id_raises() -> None:
    with pytest.raises(TTSError, match="voice_id"):
        await ElevenLabsTTS("fake-key", voice_id="").synthesize("salom")


async def test_tts_without_library_raises() -> None:
    with pytest.raises(TTSError, match="o'rnatilmagan"):
        await ElevenLabsTTS("fake-key", voice_id="v1").synthesize("salom")
