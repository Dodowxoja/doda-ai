"""``VisionProvider`` porti uchun contract."""

from __future__ import annotations

from doda.core.interfaces.perception import VisionProvider
from doda.core.models.media import MediaFrame


class VisionProviderContract:
    """VisionProvider kelishuvi (subklass ``make_provider()``ni beradi)."""

    def make_provider(self) -> VisionProvider:
        raise NotImplementedError

    def test_name_is_nonempty(self) -> None:
        assert self.make_provider().name != ""

    async def test_capture_returns_frame(self) -> None:
        frame = await self.make_provider().capture()
        assert isinstance(frame, MediaFrame)
        assert frame.media_type != ""
        assert frame.source != ""
