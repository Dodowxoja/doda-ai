"""``VoicePipeline`` — ovoz quvuri: wake → mikrofon → STT → Agent → TTS → karnay.

Bir navbat (``listen_once``): wake-so'zni kutadi, audio yozadi, matnga aylantiradi, Agentga
beradi, javobni ovozga aylantirib ijro etadi. Har bosqichda ``voice.*`` eventlari chiqadi.
Doimiy tinglash (loop) M12 (Daemon) da bu metodni takrorlaydi.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from uuid import uuid4

from doda.core.interfaces.agent import Agent
from doda.core.interfaces.bus import EventBus
from doda.core.interfaces.observability import Observability
from doda.core.interfaces.voice import (
    AudioInput,
    AudioOutput,
    SpeechToText,
    TextToSpeech,
    WakeWordDetector,
)
from doda.core.models.event import Event

_SOURCE = "voice"


class VoicePipeline:
    """Ovoz orqali bitta suhbat navbatini boshqaruvchi quvur."""

    def __init__(
        self,
        *,
        wake: WakeWordDetector,
        audio_input: AudioInput,
        stt: SpeechToText,
        agent: Agent,
        tts: TextToSpeech,
        audio_output: AudioOutput,
        events: EventBus,
        observability: Observability | None = None,
        language: str = "uz",
        record_seconds: float = 5.0,
    ) -> None:
        self._wake = wake
        self._audio_input = audio_input
        self._stt = stt
        self._agent = agent
        self._tts = tts
        self._audio_output = audio_output
        self._events = events
        self._obs = observability
        self._language = language
        self._record_seconds = record_seconds

    async def listen_once(self) -> str:
        """Bitta ovozli navbatni bajaradi va Agent javob matnini qaytaradi."""
        trace_id = uuid4().hex
        await self._wake.wait_for_wake()
        await self._emit("voice.wake", {}, trace_id)

        audio = await self._audio_input.record(seconds=self._record_seconds)
        text = await self._stt.transcribe(audio, language=self._language)
        await self._emit("voice.transcribed", {"text": text}, trace_id)

        response = await self._agent.handle(text)
        await self._emit("voice.response", {"text": response}, trace_id)

        speech = await self._tts.synthesize(response)
        await self._audio_output.play(speech)
        await self._emit("voice.spoken", {"chars": len(response)}, trace_id)
        return response

    async def _emit(self, name: str, payload: Mapping[str, Any], trace_id: str) -> None:
        await self._events.publish(
            Event(name=name, payload=payload, trace_id=trace_id, source=_SOURCE)
        )
        if self._obs is not None:
            self._obs.log("debug", f"voice event: {name}")
