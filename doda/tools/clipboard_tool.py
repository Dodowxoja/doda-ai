"""``ClipboardTool`` — clipboard'ni o'qish/yozish asbobi (macOS pbpaste/pbcopy)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from doda.tools.runner import CommandRunner, subprocess_run

_MAX_CHARS = 2000

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["read", "write"]},
        "text": {"type": "string", "description": "write uchun clipboard'ga yoziladigan matn"},
    },
    "required": ["action"],
}


class ClipboardTool:
    """Clipboard'ni o'qiydi (``pbpaste``) yoki yozadi (``pbcopy``). Runner DI orqali."""

    def __init__(self, *, runner: CommandRunner = subprocess_run) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "clipboard"

    @property
    def description(self) -> str:
        return "Clipboard matnini o'qiydi (action=read) yoki unga yozadi (action=write, text)."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _SCHEMA

    async def run(self, arguments: Mapping[str, Any]) -> str:
        action = arguments.get("action")
        if action == "read":
            result = await self._run(["pbpaste"], None)
            return result.stdout[:_MAX_CHARS]
        if action == "write":
            text = str(arguments.get("text", ""))
            await self._run(["pbcopy"], text)
            return "Clipboard yangilandi"
        raise ValueError(f"noma'lum action: '{action}' (read yoki write kutildi)")
