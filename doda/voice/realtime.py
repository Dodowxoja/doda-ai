"""``RealtimeVoiceSession`` — VAD-boshqariladigan realtime ovoz suhbati (barge-in bilan).

Oqim: mikrofon oqimi → VAD (nutq boshlandi/tugadi) → STT → **Agent** (M4/M6 → Claude) → TTS →
karnay. Har bosqichda holat-mashina (``VoiceSession``) va ``voice.*`` eventlari; latency
metrikalari kuzatiladi. Barge-in: DODA gapirayotganda ``interrupt()`` chaqirilsa, ijro uziladi.
Barcha komponentlar DI orqali — soxta variantlar bilan to'liq test qilinadi (kalitsiz).
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Mapping
from time import perf_counter
from typing import Any, TypeVar

from doda.core.interfaces.agent import Agent
from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.observability import Observability
from doda.core.interfaces.voice import (
    AudioOutput,
    SpeechToText,
    StreamingAudioInput,
    TextToSpeech,
    VoiceActivityDetector,
)
from doda.core.models.event import Event
from doda.core.models.speech import VoiceState
from doda.voice.session import VoiceSession

_SOURCE = "voice"
_T = TypeVar("_T")


async def _aclose(stream: AsyncIterator[Any]) -> None:
    """Async-oqim generator bo'lsa uni yopadi (break'dan keyin resurs sizmasin)."""
    aclose = getattr(stream, "aclose", None)
    if aclose is not None:
        await aclose()


class RealtimeVoiceSession:
    """VAD-boshqariladigan realtime ovoz suhbati (bir navbat = ``run_turn``)."""

    def __init__(
        self,
        *,
        audio_stream: StreamingAudioInput,
        vad: VoiceActivityDetector,
        stt: SpeechToText,
        agent: Agent,
        tts: TextToSpeech,
        audio_output: AudioOutput,
        events: EventBus,
        session: VoiceSession | None = None,
        observability: Observability | None = None,
        language: str = "uz",
        silence_frames: int = 3,
    ) -> None:
        self._audio_stream = audio_stream
        self._vad = vad
        self._stt = stt
        self._agent = agent
        self._tts = tts
        self._audio_output = audio_output
        self._events = events
        self._session = session or VoiceSession(events, observability=observability)
        self._obs = observability
        self._language = language
        self._silence_frames = silence_frames
        self._play_task: asyncio.Task[None] | None = None

    @property
    def session(self) -> VoiceSession:
        """Holat-mashina (tashqi kuzatuv/UI uchun)."""
        return self._session

    async def run_turn(self) -> str | None:
        """Bitta ovozli navbatni bajaradi; javob matnini (yoki None) qaytaradi."""
        started = perf_counter()
        self._metric("voice_sessions_total")
        try:
            await self._begin_listening()
            audio = await self._capture_utterance()
            if not audio:
                await self._session.reset()
                return None

            await self._session.transition(VoiceState.PROCESSING)
            text, stt_ms = await self._timed(self._stt.transcribe(audio, language=self._language))
            self._metric("stt_latency_ms", stt_ms)
            await self._emit("voice.final_transcript", {"text": text})
            if not text.strip():
                await self._session.reset()
                return None

            await self._session.transition(VoiceState.THINKING)
            await self._emit("voice.thinking", {})
            response, agent_ms = await self._timed(self._agent.handle(text))
            self._metric("agent_latency_ms", agent_ms)

            await self._session.transition(VoiceState.SPEAKING)
            await self._emit("voice.speaking", {"text": response})
            if await self._speak(response):
                return None  # barge-in bilan uzildi

            await self._session.reset()
            self._metric("voice_session_duration", (perf_counter() - started) * 1000)
            await self._emit("voice.completed", {"chars": len(response)})
            return response
        except Exception as exc:
            self._metric("voice_errors_total")
            if self._obs is not None:
                self._obs.log("error", "voice turn xato", error=repr(exc))
            await self._session.fail()
            await self._emit("voice.error", {"error": repr(exc)})
            await self._session.reset()
            return None

    async def interrupt(self) -> bool:
        """Barge-in: joriy ijroni uzadi va sessiyani tinglashga qaytaradi."""
        if self._play_task is not None and not self._play_task.done():
            self._play_task.cancel()
        return await self._session.interrupt()

    async def _begin_listening(self) -> None:
        await self._session.reset()
        await self._session.transition(VoiceState.LISTENING)
        await self._emit("voice.started", {"session_id": self._session.session_id})

    async def _capture_utterance(self) -> bytes:
        """VAD orqali nutqni yig'adi: nutq boshlanib, keyin jimlik kelsa to'xtaydi."""
        frames: list[bytes] = []
        speech_started = False
        trailing_silence = 0
        stream = self._audio_stream.stream()
        try:
            async for chunk in stream:
                is_speech = await self._vad.is_speech(chunk.audio)
                if is_speech:
                    speech_started = True
                    trailing_silence = 0
                    frames.append(chunk.audio)
                elif speech_started:
                    trailing_silence += 1
                    frames.append(chunk.audio)
                    if trailing_silence >= self._silence_frames:
                        break
                if chunk.is_last:
                    break
        finally:
            await _aclose(stream)
        return b"".join(frames)

    async def _speak(self, response: str) -> bool:
        """Javobni ovozga aylantirib ijro etadi; barge-in bo'lsa ``True``."""
        speech, tts_ms = await self._timed(self._tts.synthesize(response))
        self._metric("tts_latency_ms", tts_ms)
        self._play_task = asyncio.create_task(self._audio_output.play(speech))
        try:
            await self._play_task
        except asyncio.CancelledError:
            await self._emit("voice.interrupted", {})
            return True
        finally:
            self._play_task = None
        return False

    async def _timed(self, coro: Awaitable[_T]) -> tuple[_T, float]:
        start = perf_counter()
        result = await coro
        return result, (perf_counter() - start) * 1000.0

    def _metric(self, name: str, value: float = 1.0) -> None:
        if self._obs is not None:
            self._obs.metric(name, value)

    async def _emit(self, name: str, payload: Mapping[str, Any]) -> None:
        await self._events.publish(Event(name=name, payload=payload, source=_SOURCE))
