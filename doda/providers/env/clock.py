"""``ClockSensor`` — joriy vaqt sensori (sof, bog'liqliksiz)."""

from __future__ import annotations

from datetime import UTC, datetime


class ClockSensor:
    """Joriy UTC vaqtini beruvchi muhit sensori."""

    @property
    def name(self) -> str:
        return "clock"

    async def read(self) -> str:
        return datetime.now(UTC).isoformat()
