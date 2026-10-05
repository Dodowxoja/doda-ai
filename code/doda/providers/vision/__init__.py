"""Kamera providerlari: Mac/USB/RTSP/IP — bir xil VisionProvider (almashsa kod tegilmaydi)."""

from __future__ import annotations

from code.doda.providers.vision.factory import build_vision_provider
from code.doda.providers.vision.fake import FakeVisionProvider
from code.doda.providers.vision.mac_camera import MacCameraProvider
from code.doda.providers.vision.screen import ScreenCaptureProvider

__all__ = [
    "FakeVisionProvider",
    "MacCameraProvider",
    "ScreenCaptureProvider",
    "build_vision_provider",
]
