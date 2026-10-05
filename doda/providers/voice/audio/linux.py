"""Linux audio adapterlari — mikrofon (``arecord``) va karnay (``aplay``). Runner DI orqali."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from code.doda.providers.voice.runner import FileRunner, subprocess_to_file


class LinuxRecorder:
    """Linux mikrofonidan audio yozadi (ALSA ``arecord``)."""

    def __init__(self, *, runner: FileRunner = subprocess_to_file) -> None:
        self._run = runner

    async def record(self, *, seconds: float = 5.0) -> bytes:
        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        path = Path(name)
        command = ["arecord", "-d", str(int(seconds)), "-f", "cd", "-t", "wav", str(path)]
        try:
            await self._run(command, path)
            return await asyncio.to_thread(path.read_bytes)
        finally:
            await asyncio.to_thread(path.unlink, True)


class LinuxPlayer:
    """Audio baytlarini ``aplay`` bilan ijro etadi."""

    def __init__(self, *, runner: FileRunner = subprocess_to_file) -> None:
        self._run = runner

    async def play(self, audio: bytes) -> None:
        fd, name = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        path = Path(name)
        await asyncio.to_thread(path.write_bytes, audio)
        try:
            await self._run(["aplay", str(path)], path)
        finally:
            await asyncio.to_thread(path.unlink, True)
