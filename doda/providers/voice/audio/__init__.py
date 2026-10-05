"""Audio provayderlari — OS-specific mikrofon/karnay + streaming adapter + soxta."""

from doda.providers.voice.audio.fake import (
    FakeAudioInput,
    FakeAudioOutput,
    FakeStreamingAudioInput,
)
from doda.providers.voice.audio.linux import LinuxPlayer, LinuxRecorder
from doda.providers.voice.audio.macos import (
    AfplayOutput,
    FfmpegRecorder,
    MacPlayer,
    MacRecorder,
)
from doda.providers.voice.audio.stream import FrameStreamAdapter
from doda.providers.voice.audio.windows import WindowsPlayer, WindowsRecorder

__all__ = [
    "AfplayOutput",
    "FakeAudioInput",
    "FakeAudioOutput",
    "FakeStreamingAudioInput",
    "FfmpegRecorder",
    "FrameStreamAdapter",
    "LinuxPlayer",
    "LinuxRecorder",
    "MacPlayer",
    "MacRecorder",
    "WindowsPlayer",
    "WindowsRecorder",
]
