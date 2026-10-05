"""``MacCameraProvider`` — macOS FaceTime kamerasidan (ffmpeg avfoundation) kadr oladi."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

from code.doda.core.models.media import MediaFrame
from code.doda.providers.vision.runner import CaptureRunner, subprocess_capture


class MacCameraProvider:
    """Mac kamerasidan bitta kadr (ffmpeg avfoundation). Runner DI orqali (test uchun)."""

    def __init__(self, *, device: str = "0", runner: CaptureRunner = subprocess_capture) -> None:
        self._device = device
        self._run = runner

    @property
    def name(self) -> str:
        return "mac_camera"

    async def capture(self) -> MediaFrame:
        fd, name = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        path = Path(name)
        command = [
            "ffmpeg",
            "-y",
            "-f",
            "avfoundation",
            "-framerate",
            "30",
            "-video_size",
            "1280x720",
            "-i",
            self._device,
            "-frames:v",
            "1",
            str(path),
        ]
        try:
            await self._run(command, path)
            data = await asyncio.to_thread(path.read_bytes)
        finally:
            await asyncio.to_thread(path.unlink, missing_ok=True)
        return MediaFrame(media_type="image/jpeg", data=data, source="mac_camera")
