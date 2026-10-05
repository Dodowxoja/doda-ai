"""Kadr olish uchun subprocess-runner (tashqi chegara — DI orqali almashtiriladi).

Kamera/ekran buyrug'i ``output_path``ga yozadi. Bu funksiya haqiqiy subprocess'ni ishga
tushiradi; testlarda soxta runner injekt qilinadi (buyruq qurilishi va faylni o'qish tekshiriladi).
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

CaptureRunner = Callable[[Sequence[str], Path], Awaitable[None]]
"""Buyruqni ishga tushirib, natijani ``output_path``ga yozadigan runner turi."""


async def subprocess_capture(command: Sequence[str], output_path: Path) -> None:  # pragma: no cover
    """Buyruqni haqiqiy subprocess sifatida ishga tushiradi (chiqishni yutadi)."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await process.communicate()
