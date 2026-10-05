"""``FakeVisionProvider`` — deterministik test-provayderi (tarmoqsiz, hardware'siz)."""

from __future__ import annotations

from code.doda.core.models.media import MediaFrame


class FakeVisionProvider:
    """VisionProvider portining soxta implementatsiyasi (test uchun)."""

    def __init__(self, *, name: str = "fake", frame: MediaFrame | None = None) -> None:
        self._name = name
        self._frame = frame or MediaFrame(media_type="image/png", data=b"FAKE", source=name)

    @property
    def name(self) -> str:
        return self._name

    async def capture(self) -> MediaFrame:
        return self._frame
