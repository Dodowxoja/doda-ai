"""``FrameStreamAdapter`` + ``FakeStreamingSTT`` testlari."""

from __future__ import annotations

from collections.abc import AsyncIterator

from doda.providers.voice import FakeAudioInput, FrameStreamAdapter
from doda.providers.voice.stt import FakeStreamingSTT


async def test_frame_stream_yields_bounded_chunks() -> None:
    adapter = FrameStreamAdapter(FakeAudioInput(audio=b"MIC"), max_frames=3)
    chunks = [chunk async for chunk in adapter.stream()]
    assert len(chunks) == 3
    assert chunks[-1].is_last is True
    assert chunks[0].audio == b"MIC"
    assert chunks[0].is_last is False


async def test_streaming_stt_partial_then_final() -> None:
    async def audio() -> AsyncIterator[bytes]:
        yield b"f1"
        yield b"f2"

    stt = FakeStreamingSTT(partials=("sa", "salom"), final="salom doda")
    results = [r async for r in stt.transcribe_stream(audio())]
    assert [r.is_final for r in results] == [False, False, True]
    assert results[-1].text == "salom doda"
