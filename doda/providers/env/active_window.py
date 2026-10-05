"""``ActiveWindowSensor`` — aktiv (frontmost) ilova nomi (macOS ``osascript``)."""

from __future__ import annotations

from doda.providers.env.runner import TextRunner, subprocess_text

_SCRIPT = (
    'tell application "System Events" to name of first application process '
    "whose frontmost is true"
)


class ActiveWindowSensor:
    """Frontmost ilova nomini beruvchi sensor (runner DI orqali)."""

    def __init__(self, *, runner: TextRunner = subprocess_text) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "active_window"

    async def read(self) -> str:
        return (await self._run(["osascript", "-e", _SCRIPT])).strip()
