"""Kamera providerlari: Mac/USB/RTSP/IP — bir xil VisionProvider (almashsa kod tegilmaydi)."""

from __future__ import annotations

from doda.providers.vision.factory import build_vision_provider
from doda.providers.vision.fake import FakeVisionProvider
from doda.providers.vision.mac_camera import MacCameraProvider
from doda.providers.vision.screen import ScreenCaptureProvider

__all__ = [
    "FakeVisionProvider",
    "MacCameraProvider",
    "ScreenCaptureProvider",
    "build_vision_provider",
]
