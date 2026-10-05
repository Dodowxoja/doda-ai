"""``RealtimeVoiceSession`` testi — VAD capture, to'liq navbat, xato, barge-in."""

from __future__ import annotations

import asyncio

from code.doda.core.models.event import Event
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.observability import BasicObservability
from code.doda.providers.voice import (
    FakeAudioOutput,
    FakeStreamingAudioInput,
    FakeTTS,
    FakeVAD,
)
from code.doda.providers.voice.stt import FakeSTT
from code.doda.voice import RealtimeVoiceSession


class EchoAgent:
    async def handle(self, user_text: str) -> str:
        return f"javob: {user_text}"


class FailingSTT:
    async def transcribe(self, audio: bytes, *, language: str = "uz") -> str:
        raise RuntimeError("STT portladi")


def _rts(
    *,
    vad: FakeVAD,
    stt: object,
    tts: FakeTTS,
    output: FakeAudioOutput,
    events: AsyncioEventBus,
    obs: BasicObservability | None = None,
    frames: int = 5,
) -> RealtimeVoiceSession:
    stream = FakeStreamingAudioInput(frames=[b"a", b"b", b"c", b"d", b"e"][:frames])
    return RealtimeVoiceSession(
        audio_stream=stream,
        vad=vad,
        stt=stt,  # type: ignore[arg-type]
        agent=EchoAgent(),
        tts=tts,
        audio_output=output,
        events=events,
        observability=obs,
        silence_frames=2,
    )


async def test_full_turn_returns_response_and_metrics() -> None:
    obs = BasicObservability()
    events = AsyncioEventBus()
    seen: list[str] = []

    async def handler(event: Event) -> None:
        seen.append(event.name)

    for name in (
        "voice.started",
        "voice.final_transcript",
        "voice.thinking",
        "voice.speaking",
        "voice.completed",
    ):
        events.subscribe(name, handler)

    output = FakeAudioOutput()
    rts = _rts(
        vad=FakeVAD([True, True, False, False, False]),
        stt=FakeSTT("salom doda"),
        tts=FakeTTS(),
        output=output,
        events=events,
        obs=obs,
    )
    result = await rts.run_turn()
    assert result == "javob: salom doda"
    assert output.played == [b"audio:javob: salom doda"]
    assert seen == [
        "voice.started",
        "voice.final_transcript",
        "voice.thinking",
        "voice.speaking",
        "voice.completed",
    ]
    metrics = obs.snapshot()
    for key in ("voice_sessions_total", "stt_latency_ms", "agent_latency_ms", "tts_latency_ms"):
        assert key in metrics
    assert rts.session.state.value == "idle"


async def test_no_speech_returns_none() -> None:
    rts = _rts(
        vad=FakeVAD(False),
        stt=FakeSTT("x"),
        tts=FakeTTS(),
        output=FakeAudioOutput(),
        events=AsyncioEventBus(),
    )
    assert await rts.run_turn() is None
    assert rts.session.state.value == "idle"


async def test_empty_transcript_returns_none() -> None:
    rts = _rts(
        vad=FakeVAD([True, True, False, False]),
        stt=FakeSTT("   "),
        tts=FakeTTS(),
        output=FakeAudioOutput(),
        events=AsyncioEventBus(),
    )
    assert await rts.run_turn() is None


async def test_error_path_isolated() -> None:
    obs = BasicObservability()
    events = AsyncioEventBus()
    errors: list[str] = []

    async def handler(event: Event) -> None:
        errors.append(event.name)

    events.subscribe("voice.error", handler)
    rts = _rts(
        vad=FakeVAD([True, True, False, False]),
        stt=FailingSTT(),
        tts=FakeTTS(),
        output=FakeAudioOutput(),
        events=events,
        obs=obs,
    )
    assert await rts.run_turn() is None
    assert "voice.error" in errors
    assert obs.snapshot()["voice_errors_total"] == 1.0
    assert rts.session.state.value == "idle"


class BlockingAudioOutput:
    """Ijroni ``release`` kutib turadigan karnay (barge-in testi uchun)."""

    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def play(self, audio: bytes) -> None:
        self.started.set()
        await self.release.wait()


async def test_barge_in_interrupts_playback() -> None:
    events = AsyncioEventBus()
    interrupted: list[str] = []

    async def handler(event: Event) -> None:
        interrupted.append(event.name)

    events.subscribe("voice.interrupted", handler)
    output = BlockingAudioOutput()
    rts = _rts(
        vad=FakeVAD([True, True, False, False]),
        stt=FakeSTT("salom"),
        tts=FakeTTS(),
        output=output,  # type: ignore[arg-type]
        events=events,
    )
    task = asyncio.create_task(rts.run_turn())
    await asyncio.wait_for(output.started.wait(), timeout=2.0)
    assert rts.session.state.value == "speaking"
    assert await rts.interrupt() is True
    result = await asyncio.wait_for(task, timeout=2.0)
    assert result is None
    assert "voice.interrupted" in interrupted
    assert rts.session.state.value == "listening"
