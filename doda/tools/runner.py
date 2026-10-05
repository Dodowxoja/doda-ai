"""Asboblar uchun subprocess-runner (stdin + stderr + exit-code; DI orqali almashtiriladi).

Env sensorlaridagi sodda ``TextRunner``dan farqi: bu yerda asboblarga stdin berish
(``pbcopy``), stderr va qaytish-kodini tekshirish (``ShellTool``) kerak. Test paytida bu
runner soxta funksiya bilan almashtiriladi — hech qanday haqiqiy subprocess ishlamaydi.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Bajarilgan buyruq natijasi."""

    stdout: str
    stderr: str
    returncode: int


CommandRunner = Callable[[Sequence[str], str | None], Awaitable[CommandResult]]
"""Buyruq + ixtiyoriy stdin matnini olib, ``CommandResult`` qaytaradigan runner turi."""


async def subprocess_run(
    command: Sequence[str], stdin_text: str | None = None
) -> CommandResult:  # pragma: no cover
    """Buyruqni ishga tushiradi (ixtiyoriy stdin bilan) va natijani qaytaradi."""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE if stdin_text is not None else None,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate(
        stdin_text.encode("utf-8") if stdin_text is not None else None
    )
    return CommandResult(
        stdout=stdout.decode("utf-8", errors="replace"),
        stderr=stderr.decode("utf-8", errors="replace"),
        returncode=process.returncode or 0,
    )
