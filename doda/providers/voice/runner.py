"""Ovoz adapterlari uchun fayl-chiqaruvchi subprocess-runner (DI orqali almashtiriladi).

Ko'p ovoz buyruqlari (TTS→mp3, yozuvchi→wav, STT→txt) natijani FAYLga yozadi. ``FileRunner``
buyruqni ishga tushiradi; ``output_path`` chaqiruvchi tomonidan buyruqqa kiritilgan yo'l
(soxta runner test paytida shu yo'lga yozadi). Real subprocess chegarasi test qamrovidan
tashqarida (#pragma).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

FileRunner = Callable[[Sequence[str], Path], Awaitable[None]]
"""Buyruqni ishga tushiruvchi (natija ``output_path`` faylida bo'ladi) runner turi."""


async def subprocess_to_file(command: Sequence[str], output_path: Path) -> None:  # pragma: no cover
    """Buyruqni ishga tushiradi; natija faylini buyruqning o'zi yozadi."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()
