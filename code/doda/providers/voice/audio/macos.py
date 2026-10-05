"""macOS audio adapterlari — mikrofon (ffmpeg avfoundation) va karnay (afplay).

OS-specific kod SHU YERDA (core ichida ``if macos`` yo'q). Runner DI orqali (real subprocess
chegarasi #pragma). Bir martalik ``record``/``play`` — streaming uchun ``FrameStreamAdapter``.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from code.doda.providers.voice.runner import FileRunner, subprocess_to_file


class MacRecorder:
    """macOS mikrofonidan audio yozadi (``ffmpeg avfoundation``)."""

    def __init__(self, *, device: str = ":0", runner: FileRunner = subprocess_to_file) -> None:
        self._device = device
        self._run = runner

    async def record(self, *, seconds: float = 5.0) -> bytes:
        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        path = Path(name)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-i",
            self._device,
            "-t",
            str(seconds),
            str(path),
        ]
        try:
            await self._run(command, path)
            return await asyncio.to_thread(path.read_bytes)
        finally:
            await asyncio.to_thread(path.unlink, True)


class MacPlayer:
    """Audio baytlarini vaqtinchalik faylga yozib, ``afplay`` bilan ijro etadi."""

    def __init__(self, *, runner: FileRunner = subprocess_to_file) -> None:
        self._run = runner

    async def play(self, audio: bytes) -> None:
        fd, name = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        path = Path(name)
        await asyncio.to_thread(path.write_bytes, audio)
        try:
            await self._run(["afplay", str(path)], path)
        finally:
            await asyncio.to_thread(path.unlink, True)


# Orqaga-moslik uchun eski nomlar (M8 API'si buzilmasin).
FfmpegRecorder = MacRecorder
AfplayOutput = MacPlayer
