"""``FilesTool`` — fayllarni o'qish/ro'yxatlash/yozish asbobi (root papka bilan cheklangan).

Xavfsizlik: barcha yo'llar ``root`` papka ichida bo'lishi shart. ``..`` orqali tashqariga
chiqishga urinish rad etiladi (path-traversal himoyasi). Fayl I/O bloklovchi, shu bois
``asyncio.to_thread`` ichida (Async-First).
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_MAX_READ_CHARS = 20_000

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["read", "list", "write"]},
        "path": {"type": "string", "description": "root papkaga nisbatan yo'l"},
        "content": {"type": "string", "description": "write uchun yoziladigan matn"},
    },
    "required": ["action", "path"],
}


class FilesTool:
    """Root papka ichidagi fayllarni boshqaradi (o'qish/ro'yxat/yozish)."""

    def __init__(self, root: Path) -> None:
        """Asbobni ``root`` ish-papkasi bilan quradi (barcha amallar shu ichida)."""
        self._root = root.resolve()

    @property
    def name(self) -> str:
        return "files"

    @property
    def description(self) -> str:
        return (
            "Ish-papkadagi fayllarni o'qiydi (action=read), papkani ro'yxatlaydi "
            "(action=list) yoki faylga yozadi (action=write, content). path — nisbiy yo'l."
        )

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _SCHEMA

    def _resolve(self, path: str) -> Path:
        """``path``ni root ichida xavfsiz hal qiladi; tashqariga chiqishni rad etadi."""
        target = (self._root / path).resolve()
        if target != self._root and self._root not in target.parents:
            raise ValueError("yo'l ish-papkadan tashqarida (ruxsat berilmadi)")
        return target

    async def run(self, arguments: Mapping[str, Any]) -> str:
        action = arguments.get("action")
        target = self._resolve(str(arguments.get("path", "")))
        if action == "read":
            return await self._read(target)
        if action == "list":
            return await self._list(target)
        if action == "write":
            return await self._write(target, str(arguments.get("content", "")))
        raise ValueError(f"noma'lum action: '{action}' (read/list/write kutildi)")

    async def _read(self, target: Path) -> str:
        if not await asyncio.to_thread(target.is_file):
            raise ValueError(f"fayl topilmadi: {target.name}")
        text = await asyncio.to_thread(target.read_text, "utf-8")
        return text[:_MAX_READ_CHARS]

    async def _list(self, target: Path) -> str:
        if not await asyncio.to_thread(target.is_dir):
            raise ValueError(f"papka topilmadi: {target.name}")
        names = sorted(p.name for p in await asyncio.to_thread(lambda: list(target.iterdir())))
        return "\n".join(names) if names else "(bo'sh papka)"

    async def _write(self, target: Path, content: str) -> str:
        await asyncio.to_thread(target.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_text, content, "utf-8")
        return f"Yozildi: {target.name} ({len(content)} belgi)"
