"""Telemetriya provayderlari — real (psutil) + soxta tizim sampleri."""

from doda.providers.telemetry.fake import FakeSystemSampler
from doda.providers.telemetry.psutil_sampler import PsutilSampler

__all__ = ["FakeSystemSampler", "PsutilSampler"]
