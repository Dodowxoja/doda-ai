"""Matn qaytaruvchi subprocess-runner (env sensorlar uchun; DI orqali almashtiriladi)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence

TextRunner = Callable[[Sequence[str]], Awaitable[str]]
"""Buyruqni ishga tushirib, stdout matnini qaytaradigan runner turi."""


async def subprocess_text(command: Sequence[str]) -> str:  # pragma: no cover
    """Buyruqni ishga tushirib, stdout'ni matn sifatida qaytaradi."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate()
    return stdout.decode("utf-8", errors="replace")
