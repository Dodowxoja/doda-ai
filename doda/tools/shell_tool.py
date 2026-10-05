"""``ShellTool`` — terminal buyrug'ini bajaradigan asbob.

Bu kuchli asbob: foydalanuvchining o'z mashinasida ``/bin/sh -c <buyruq>`` ishlatadi.
Buyruq ``timeout`` bilan cheklanadi va natija (stdout/stderr/kod) matn sifatida qaytadi.
Subprocess runner DI orqali — test paytida haqiqiy buyruq ishlamaydi.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from doda.tools.runner import CommandRunner, subprocess_run

_MAX_OUTPUT_CHARS = 10_000

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "command": {"type": "string", "description": "bajariladigan shell buyrug'i"},
    },
    "required": ["command"],
}


class ShellTool:
    """Shell buyrug'ini bajaradi (``/bin/sh -c``). Runner DI orqali."""

    def __init__(self, *, runner: CommandRunner = subprocess_run) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "run_shell"

    @property
    def description(self) -> str:
        return "Terminal (shell) buyrug'ini bajaradi va stdout/stderr natijasini qaytaradi."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _SCHEMA

    async def run(self, arguments: Mapping[str, Any]) -> str:
        command = str(arguments.get("command", "")).strip()
        if not command:
            raise ValueError("bo'sh buyruq")
        result = await self._run(["/bin/sh", "-c", command], None)
        output = result.stdout.strip()
        if result.returncode != 0:
            error = result.stderr.strip() or f"buyruq {result.returncode} kodi bilan tugadi"
            return f"(xato kod {result.returncode}) {error}"[:_MAX_OUTPUT_CHARS]
        return output[:_MAX_OUTPUT_CHARS] if output else "(natija yo'q)"
