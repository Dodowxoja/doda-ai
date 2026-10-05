"""``ScreenCaptureProvider`` — macOS ``screencapture`` orqali ekran kadrini oladi."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from doda.core.models.media import MediaFrame
from doda.providers.vision.runner import CaptureRunner, subprocess_capture


class ScreenCaptureProvider:
    """Ekran surati (macOS ``screencapture``). Runner DI orqali (test uchun)."""

    def __init__(self, *, runner: CaptureRunner = subprocess_capture) -> None:
        self._run = runner

    @property
    def name(self) -> str:
        return "screen"

    async def capture(self) -> MediaFrame:
        fd, name = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        path = Path(name)
        try:
            await self._run(["screencapture", "-x", "-t", "png", str(path)], path)
            data = await asyncio.to_thread(path.read_bytes)
        finally:
            await asyncio.to_thread(path.unlink, missing_ok=True)
        return MediaFrame(media_type="image/png", data=data, source="screen")
