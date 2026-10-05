"""Windows audio adapterlari — mikrofon (ffmpeg dshow) va karnay (ffplay). Runner DI orqali."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from code.doda.providers.voice.runner import FileRunner, subprocess_to_file


class WindowsRecorder:
    """Windows mikrofonidan audio yozadi (ffmpeg ``dshow``)."""

    def __init__(
        self, *, device: str = "audio=default", runner: FileRunner = subprocess_to_file
    ) -> None:
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
            "dshow",
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


class WindowsPlayer:
    """Audio baytlarini ``ffplay`` bilan ijro etadi."""

    def __init__(self, *, runner: FileRunner = subprocess_to_file) -> None:
        self._run = runner

    async def play(self, audio: bytes) -> None:
        fd, name = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        path = Path(name)
        await asyncio.to_thread(path.write_bytes, audio)
        try:
            await self._run(["ffplay", "-nodisp", "-autoexit", str(path)], path)
        finally:
            await asyncio.to_thread(path.unlink, True)
