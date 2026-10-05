"""``ClipboardSensor`` — macOS clipboard matni (``pbpaste``)."""

from __future__ import annotations

from doda.providers.env.runner import TextRunner, subprocess_text

_MAX_CHARS = 500


class ClipboardSensor:
    """Clipboard matnini beruvchi sensor (runner DI orqali)."""

    def __init__(self, *, runner: TextRunner = subprocess_text) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "clipboard"

    async def read(self) -> str:
        text = await self._run(["pbpaste"])
        return text[:_MAX_CHARS]
