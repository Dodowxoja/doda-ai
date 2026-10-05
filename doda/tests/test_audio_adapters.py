"""Linux/Windows audio adapterlari + Whisper xato-tarmog'i testi (soxta FileRunner bilan)."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest

from doda.core.errors import STTError
from doda.providers.voice import (
    LinuxPlayer,
    LinuxRecorder,
    WhisperSTT,
    WindowsPlayer,
    WindowsRecorder,
)


def file_runner(*, writes: bytes | None = None, capture: dict[str, Any] | None = None) -> Any:
    async def runner(command: Sequence[str], output_path: Path) -> None:
        if capture is not None:
            capture["command"] = list(command)
        if writes is not None:
            output_path.write_bytes(writes)

    return runner


async def test_linux_recorder_uses_arecord() -> None:
    captured: dict[str, Any] = {}
    result = await LinuxRecorder(runner=file_runner(writes=b"WAV", capture=captured)).record(
        seconds=2.0
    )
    assert result == b"WAV"
    assert captured["command"][0] == "arecord"


async def test_linux_player_uses_aplay() -> None:
    captured: dict[str, Any] = {}
    await LinuxPlayer(runner=file_runner(capture=captured)).play(b"AUDIO")
    assert captured["command"][0] == "aplay"


async def test_windows_recorder_uses_ffmpeg_dshow() -> None:
    captured: dict[str, Any] = {}
    result = await WindowsRecorder(runner=file_runner(writes=b"WAV", capture=captured)).record()
    assert result == b"WAV"
    assert captured["command"][0] == "ffmpeg"
    assert "dshow" in captured["command"]


async def test_windows_player_uses_ffplay() -> None:
    captured: dict[str, Any] = {}
    await WindowsPlayer(runner=file_runner(capture=captured)).play(b"AUDIO")
    assert captured["command"][0] == "ffplay"


async def test_whisper_missing_output_raises() -> None:
    # Runner transkript faylini yozmasa → aniq STTError (crash emas).
    with pytest.raises(STTError, match="transkript"):
        await WhisperSTT(runner=file_runner()).transcribe(b"AUDIO")
