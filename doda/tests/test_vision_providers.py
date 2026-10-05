"""Vision providerlar testlari — contract + soxta runner bilan buyruq/kadr tekshiruvi."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from doda.core.errors import ConfigError
from doda.core.interfaces.perception import VisionProvider
from doda.providers.vision import (
    FakeVisionProvider,
    MacCameraProvider,
    ScreenCaptureProvider,
    build_vision_provider,
)
from doda.tests.contracts.vision_provider_contract import VisionProviderContract


async def _write_runner(command: Sequence[str], output_path: Path) -> None:
    output_path.write_bytes(b"IMGDATA")


class TestFakeVisionProvider(VisionProviderContract):
    def make_provider(self) -> VisionProvider:
        return FakeVisionProvider()


class TestScreenCaptureProvider(VisionProviderContract):
    def make_provider(self) -> VisionProvider:
        return ScreenCaptureProvider(runner=_write_runner)

    async def test_uses_screencapture_and_reads_bytes(self) -> None:
        captured: dict[str, list[str]] = {}

        async def runner(command: Sequence[str], output_path: Path) -> None:
            captured["cmd"] = list(command)
            output_path.write_bytes(b"PNG")

        frame = await ScreenCaptureProvider(runner=runner).capture()
        assert "screencapture" in captured["cmd"]
        assert frame.data == b"PNG"
        assert frame.media_type == "image/png"
        assert frame.source == "screen"


class TestMacCameraProvider(VisionProviderContract):
    def make_provider(self) -> VisionProvider:
        return MacCameraProvider(runner=_write_runner)

    async def test_uses_ffmpeg(self) -> None:
        captured: dict[str, list[str]] = {}

        async def runner(command: Sequence[str], output_path: Path) -> None:
            captured["cmd"] = list(command)
            output_path.write_bytes(b"JPG")

        frame = await MacCameraProvider(runner=runner).capture()
        assert "ffmpeg" in captured["cmd"]
        assert frame.source == "mac_camera"
        assert frame.media_type == "image/jpeg"


class TestBuildVisionProvider:
    def test_screen(self) -> None:
        assert isinstance(build_vision_provider("screen"), ScreenCaptureProvider)

    def test_mac_camera(self) -> None:
        assert isinstance(build_vision_provider("mac_camera"), MacCameraProvider)

    def test_unimplemented_raises(self) -> None:
        with pytest.raises(ConfigError, match=r"v2\.0"):
            build_vision_provider("rtsp")

    def test_unknown_raises(self) -> None:
        with pytest.raises(ConfigError, match="Noma'lum"):
            build_vision_provider("xyz")
