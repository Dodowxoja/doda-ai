"""``ClockTool`` — joriy sana/vaqtni beradigan asbob."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

_EMPTY_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}}


class ClockTool:
    """Joriy vaqtni ISO-8601 formatida qaytaradi (soat DI orqali — test uchun)."""

    def __init__(self, *, now: Callable[[], datetime] = datetime.now) -> None:
        self._now = now

    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return "Joriy sana va vaqtni ISO-8601 formatida qaytaradi."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return _EMPTY_SCHEMA

    async def run(self, arguments: Mapping[str, Any]) -> str:
        return self._now().isoformat(timespec="seconds")
