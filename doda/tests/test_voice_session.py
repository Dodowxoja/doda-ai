"""``VoiceSession`` holat-mashina testi — o'tishlar, barge-in, xato, eventlar."""

from __future__ import annotations

import pytest

from doda.core.errors import ConfigError
from doda.core.models.event import Event
from doda.core.models.speech import VoiceState
from doda.providers.bus import AsyncioEventBus
from doda.providers.observability import BasicObservability
from doda.voice import VoiceSession


async def test_valid_transition_flow() -> None:
    session = VoiceSession(AsyncioEventBus(), observability=BasicObservability())
    assert session.state.value == "idle"
    await session.transition(VoiceState.LISTENING)
    await session.transition(VoiceState.PROCESSING)
    await session.transition(VoiceState.THINKING)
    await session.transition(VoiceState.SPEAKING)
    assert session.state.value == "speaking"


async def test_invalid_transition_raises() -> None:
    session = VoiceSession(AsyncioEventBus())
    with pytest.raises(ConfigError, match="noto'g'ri o'tish"):
        await session.transition(VoiceState.SPEAKING)  # IDLE → SPEAKING taqiqlangan


async def test_barge_in_from_speaking() -> None:
    session = VoiceSession(AsyncioEventBus())
    await session.transition(VoiceState.LISTENING)
    await session.transition(VoiceState.PROCESSING)
    await session.transition(VoiceState.THINKING)
    await session.transition(VoiceState.SPEAKING)
    assert await session.interrupt() is True
    assert session.state.value == "listening"


async def test_interrupt_ignored_when_not_speaking() -> None:
    session = VoiceSession(AsyncioEventBus())
    assert await session.interrupt() is False


async def test_fail_and_reset() -> None:
    session = VoiceSession(AsyncioEventBus())
    await session.fail()
    assert session.state.value == "error"
    await session.fail()  # ikkinchi marta — no-op
    await session.reset()
    assert session.state.value == "idle"
    await session.reset()  # allaqachon IDLE — no-op


async def test_emits_state_events() -> None:
    events = AsyncioEventBus()
    seen: list[tuple[str, str]] = []

    async def handler(event: Event) -> None:
        seen.append((event.payload["from"], event.payload["to"]))

    events.subscribe("voice.state", handler)
    session = VoiceSession(events, session_id="s1")
    await session.transition(VoiceState.LISTENING)
    assert seen == [("idle", "listening")]
    assert session.session_id == "s1"
