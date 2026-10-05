"""``OpenTool`` — macOS ``open`` bilan URL / ilova / faylni ochadi.

"YouTube'ni och", "brauzerni och", "kalkulyatorni och" kabi so'rovlar uchun. Domen ko'rinishidagi
matn (``youtube.com``) avtomatik ``https://`` bilan URL'ga aylantiriladi; ilova nomi bo'lsa
``open -a`` ishlatiladi. Runner DI orqali (test uchun soxta).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from doda.tools.runner import CommandRunner, subprocess_run

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "target": {
            "type": "string",
            "description": "URL (https://youtube.com), ilova nomi (Safari) yoki fayl yo'li",
        }
    },
    "required": ["target"],
}


class OpenTool:
    """URL, ilova yoki faylni ochadi (macOS ``open``). Runner DI orqali."""

    def __init__(self, *, runner: CommandRunner = subprocess_run) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "open"

    @property
    def description(self) -> str:
        return "URL, ilova yoki faylni ochadi — masalan YouTube, brauzer, kalkulyator, papka."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _SCHEMA

    async def run(self, arguments: Mapping[str, Any]) -> str:
        target = str(arguments.get("target", "")).strip()
        if not target:
            raise ValueError("bo'sh target")
        first = target.split("/", 1)[0]
        if "://" not in target and "." in first and " " not in first:
            target = "https://" + target  # domen ko'rinishi → to'liq URL
        if "://" in target or target.startswith("/") or "." in target:
            command = ["open", target]
        else:
            command = ["open", "-a", target]  # ilova nomi
        result = await self._run(command, None)
        if result.returncode != 0:
            return f"(ochib bo'lmadi: {result.stderr.strip() or target})"
        return f"Ochildi: {target}"
