"""``WhisperSTT`` — ``whisper`` CLI orqali ovozdan matnga (o'zbek tili ustuvor).

Audio vaqtinchalik faylga yoziladi, ``whisper`` uni transkripsiya qilib ``.txt`` chiqaradi,
so'ng o'qiladi. Runner DI orqali (real subprocess chegarasi #pragma). Bir martalik (non-stream)
provider — real-vaqt uchun ``ElevenLabsSTT`` yoki kelajakdagi streaming adapter ishlatiladi.
"""

from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path

from code.doda.core.errors import STTError
from code.doda.providers.voice.runner import FileRunner, subprocess_to_file


class WhisperSTT:
    """Audio baytlarini whisper orqali matnga aylantiradi."""

    def __init__(self, *, model: str = "small", runner: FileRunner = subprocess_to_file) -> None:
        self._model = model
        self._run = runner

    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        directory = Path(tempfile.mkdtemp())
        audio_path = directory / "input.wav"
        text_path = directory / "input.txt"
        await asyncio.to_thread(audio_path.write_bytes, audio)
        command = [
            "whisper",
            str(audio_path),
            "--model",
            self._model,
            "--language",
            language,
            "--output_format",
            "txt",
            "--output_dir",
            str(directory),
        ]
        try:
            await self._run(command, text_path)
            if not await asyncio.to_thread(text_path.is_file):
                raise STTError("whisper transkript faylini yaratmadi")
            text = await asyncio.to_thread(text_path.read_text, "utf-8")
            return text.strip()
        finally:
            await asyncio.to_thread(_cleanup, directory)


def _cleanup(directory: Path) -> None:
    """Vaqtinchalik papkani (fayllari bilan) o'chiradi."""
    shutil.rmtree(directory, ignore_errors=True)
