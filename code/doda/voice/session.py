"""``VoiceSession`` — ovoz sessiyasining holat-mashinasi (barge-in bilan).

Holatlar: IDLE→LISTENING→PROCESSING→THINKING→SPEAKING→IDLE. DODA gapirayotganda user
gapirsa: SPEAKING→INTERRUPTED→LISTENING (barge-in). Noto'g'ri o'tishlar rad etiladi
(``ConfigError``). Har o'tishda ``voice.state`` eventi chiqadi (dashboard/kuzatuv uchun).
"""

from __future__ import annotations

from uuid import uuid4

from code.doda.core.errors import ConfigError
from code.doda.core.interfaces.bus import EventBus
from code.doda.core.interfaces.observability import Observability
from code.doda.core.models.event import Event
from code.doda.core.models.speech import VoiceState

_SOURCE = "voice"

#: Ruxsat etilgan holat o'tishlari (state machine grafi).
_ALLOWED: dict[VoiceState, frozenset[VoiceState]] = {
    VoiceState.IDLE: frozenset({VoiceState.LISTENING, VoiceState.ERROR}),
    VoiceState.LISTENING: frozenset({VoiceState.PROCESSING, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.PROCESSING: frozenset({VoiceState.THINKING, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.THINKING: frozenset({VoiceState.SPEAKING, VoiceState.IDLE, VoiceState.ERROR}),
    VoiceState.SPEAKING: frozenset({VoiceState.IDLE, VoiceState.INTERRUPTED, VoiceState.ERROR}),
    VoiceState.INTERRUPTED: frozenset({VoiceState.LISTENING, VoiceState.IDLE}),
    VoiceState.ERROR: frozenset({VoiceState.IDLE}),
}


class VoiceSession:
    """Ovoz sessiyasi holat-mashinasi (bitta suhbat sessiyasi)."""

    def __init__(
        self,
        events: EventBus,
        *,
        session_id: str | None = None,
        observability: Observability | None = None,
    ) -> None:
        self.session_id = session_id or uuid4().hex
        self._events = events
        self._obs = observability
        self._state = VoiceState.IDLE

    @property
    def state(self) -> VoiceState:
        """Joriy holat."""
        return self._state

    async def transition(self, to: VoiceState) -> None:
        """``to`` holatiga o'tadi (ruxsat etilmagan o'tish → ``ConfigError``)."""
        if to not in _ALLOWED[self._state]:
            raise ConfigError(f"noto'g'ri o'tish: {self._state} → {to}")
        previous = self._state
        self._state = to
        await self._events.publish(
            Event(
                name="voice.state",
                payload={"from": str(previous), "to": str(to), "session_id": self.session_id},
                source=_SOURCE,
            )
        )
        if self._obs is not None:
            self._obs.log("debug", f"voice state: {previous} → {to}")

    async def interrupt(self) -> bool:
        """Barge-in: DODA gapirayotgan bo'lsa uzib, tinglashga qaytadi. Muvaffaqiyatda ``True``."""
        if self._state != VoiceState.SPEAKING:
            return False
        await self.transition(VoiceState.INTERRUPTED)
        await self.transition(VoiceState.LISTENING)
        return True

    async def fail(self) -> None:
        """Xato holatiga o'tadi (agar allaqachon ERROR bo'lmasa)."""
        if self._state != VoiceState.ERROR:
            await self.transition(VoiceState.ERROR)

    async def reset(self) -> None:
        """IDLE holatiga qaytaradi (agar allaqachon IDLE bo'lmasa)."""
        if self._state != VoiceState.IDLE:
            await self.transition(VoiceState.IDLE)
