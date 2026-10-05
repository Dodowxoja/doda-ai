"""VAD testlari — EnergyVAD (dep-siz), FakeVAD, SileroVAD (torch yo'q → xato)."""

from __future__ import annotations

from array import array

import pytest

from doda.core.errors import VADError
from doda.core.interfaces.voice import VoiceActivityDetector
from doda.providers.voice.vad import EnergyVAD, FakeVAD, SileroVAD
from doda.tests.contracts.voice_contracts import VADContract


class TestEnergyVADContract(VADContract):
    def make_vad(self) -> VoiceActivityDetector:
        return EnergyVAD()


class TestFakeVADContract(VADContract):
    def make_vad(self) -> VoiceActivityDetector:
        return FakeVAD()


def _pcm(amplitude: int, samples: int = 160) -> bytes:
    return array("h", [amplitude] * samples).tobytes()


# ---------------- EnergyVAD ----------------


async def test_energy_detects_loud_as_speech() -> None:
    vad = EnergyVAD(threshold=500.0)
    assert await vad.is_speech(_pcm(5000)) is True


async def test_energy_detects_quiet_as_silence() -> None:
    vad = EnergyVAD(threshold=500.0)
    assert await vad.is_speech(_pcm(10)) is False


async def test_energy_short_frame_is_silence() -> None:
    assert await EnergyVAD().is_speech(b"") is False
    assert await EnergyVAD().is_speech(b"\x01") is False  # 1 bayt (int16 uchun yetarli emas)


def test_energy_reset_is_noop() -> None:
    EnergyVAD().reset()  # xato bermasligi kifoya


# ---------------- FakeVAD ----------------


async def test_fake_fixed_result() -> None:
    assert await FakeVAD(True).is_speech(b"x") is True
    assert await FakeVAD(False).is_speech(b"x") is False


async def test_fake_sequence_and_reset() -> None:
    vad = FakeVAD([True, False, True])
    assert await vad.is_speech(b"") is True
    assert await vad.is_speech(b"") is False
    vad.reset()
    assert vad.resets == 1
    assert await vad.is_speech(b"") is True  # reset qaytadan boshladi


# ---------------- SileroVAD ----------------


async def test_silero_without_torch_raises() -> None:
    # torch o'rnatilmagan muhitda aniq VADError (crash emas).
    with pytest.raises(VADError, match="torch"):
        await SileroVAD().is_speech(_pcm(5000))


def test_silero_reset_without_model_is_noop() -> None:
    SileroVAD().reset()  # model yuklanmagan — xato bermaydi
