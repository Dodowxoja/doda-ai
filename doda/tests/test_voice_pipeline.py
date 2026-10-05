"""``VoicePipeline`` testi — bir navbat: wake→record→STT→Agent→TTS→play + eventlar."""

from __future__ import annotations

from code.doda.core.models.event import Event
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.observability import BasicObservability
from code.doda.providers.voice import (
    FakeAudioInput,
    FakeAudioOutput,
    FakeSTT,
    FakeTTS,
    FakeWakeWord,
)
from code.doda.voice import VoicePipeline


class EchoAgent:
    async def handle(self, user_text: str) -> str:
        return f"javob: {user_text}"


def _make_pipeline(
    events: AsyncioEventBus, stt: FakeSTT, tts: FakeTTS, out: FakeAudioOutput
) -> VoicePipeline:
    return VoicePipeline(
        wake=FakeWakeWord(),
        audio_input=FakeAudioInput(audio=b"MIC"),
        stt=stt,
        agent=EchoAgent(),
        tts=tts,
        audio_output=out,
        events=events,
        observability=BasicObservability(),
    )


async def test_listen_once_returns_agent_response() -> None:
    pipeline = _make_pipeline(AsyncioEventBus(), FakeSTT("salom"), FakeTTS(), FakeAudioOutput())
    assert await pipeline.listen_once() == "javob: salom"


async def test_pipeline_wires_audio_through_stages() -> None:
    stt = FakeSTT("salom")
    tts = FakeTTS()
    out = FakeAudioOutput()
    pipeline = _make_pipeline(AsyncioEventBus(), stt, tts, out)
    await pipeline.listen_once()
    assert stt.calls == [b"MIC"]  # yozilgan audio STT'ga uzatildi
    assert tts.spoken == ["javob: salom"]  # agent javobi TTS'ga uzatildi
    assert out.played == [b"audio:javob: salom"]  # sintez qilingan audio ijro etildi


async def test_emits_voice_events() -> None:
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    for name in ("voice.wake", "voice.transcribed", "voice.response", "voice.spoken"):
        events.subscribe(name, handler)
    await _make_pipeline(events, FakeSTT("salom"), FakeTTS(), FakeAudioOutput()).listen_once()
    assert seen == ["voice.wake", "voice.transcribed", "voice.response", "voice.spoken"]
