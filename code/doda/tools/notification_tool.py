"""``NotificationTool`` — macOS tizim bildirishnomasini yuboradigan asbob (osascript)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from code.doda.tools.runner import CommandRunner, subprocess_run

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "bildirishnoma sarlavhasi"},
        "message": {"type": "string", "description": "bildirishnoma matni"},
    },
    "required": ["message"],
}


def _sanitize(text: str) -> str:
    """osascript qatori ichidagi qo'shtirnoq/yangi-qatorlarni zararsizlantiradi."""
    return text.replace('"', "'").replace("\n", " ").replace("\\", "")


class NotificationTool:
    """macOS bildirishnoma chiqaradi (``osascript``). Runner DI orqali."""

    def __init__(self, *, runner: CommandRunner = subprocess_run) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "send_notification"

    @property
    def description(self) -> str:
        return "Foydalanuvchiga macOS tizim bildirishnomasini yuboradi (title, message)."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _SCHEMA

    async def run(self, arguments: Mapping[str, Any]) -> str:
        message = _sanitize(str(arguments.get("message", "")))
        title = _sanitize(str(arguments.get("title", "DODA")))
        script = f'display notification "{message}" with title "{title}"'
        result = await self._run(["osascript", "-e", script], None)
        if result.returncode != 0:
            raise RuntimeError(f"bildirishnoma yuborilmadi: {result.stderr.strip()}")
        return "Bildirishnoma yuborildi"
