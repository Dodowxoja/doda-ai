"""``EdgeTTS`` — Microsoft Edge TTS (``edge-tts`` CLI) orqali ovoz sintezi (DEFAULT).

O'zbekcha ovoz ustuvor (``uz-UZ-SardorNeural`` / ``uz-UZ-MadinaNeural``) — foydalanuvchi
ingliz-ovoz o'zbekchani yomon talaffuz qilishidan shikoyat qilgan edi. Runner DI orqali.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from code.doda.providers.voice.runner import FileRunner, subprocess_to_file

DEFAULT_VOICE = "uz-UZ-SardorNeural"


class EdgeTTS:
    """Matnni edge-tts orqali audioga (mp3) aylantiradi."""

    def __init__(
        self, *, voice: str = DEFAULT_VOICE, runner: FileRunner = subprocess_to_file
    ) -> None:
        self._voice = voice
        self._run = runner

    async def synthesize(self, text: str) -> bytes:
        fd, name = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
        path = Path(name)
        command = ["edge-tts", "--voice", self._voice, "--text", text, "--write-media", str(path)]
        try:
            await self._run(command, path)
            return await asyncio.to_thread(path.read_bytes)
        finally:
            await asyncio.to_thread(path.unlink, True)
