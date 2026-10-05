"""Telemetriya provayderlari — real (psutil) + soxta tizim sampleri."""

from code.doda.providers.telemetry.fake import FakeSystemSampler
from code.doda.providers.telemetry.psutil_sampler import PsutilSampler

__all__ = ["FakeSystemSampler", "PsutilSampler"]
