"""``CommandRouter`` — dashboarddan kelgan buyruqlarni Agentga yo'naltiradi.

Klient ``{"type":"chat","text":"..."}`` yuborsa, matn **bitta `Agent`** ga beriladi (chat va
voice bir xil pipeline). Agent EventBus'ga eventlar chiqaradi, ular ``EventBridge`` orqali
dashboardga qaytadi. Streaming yoqilgan va agent qo'llab-quvvatlasa, javob bo'lak-bo'lak keladi.

Xatolar (kalit yo'q / noto'g'ri / timeout) **aniq, foydalanuvchiga tushunarli** xabarga
aylantiriladi — jim qolmaydi va API kaliti hech qachon xabar ichida chiqmaydi.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from code.doda.core.errors import LLMError, LLMUnavailableError
from code.doda.core.interfaces.agent import Agent, StreamingAgent
from code.doda.core.interfaces.observability import Observability
from code.doda.interfaces.api.protocol import ClientMessage

_KEY_MISSING = (
    "⚠️ Claude API kaliti sozlanmagan. SecretStore'ga 'anthropic.key' qo'ying "
    "(env: DODA_SECRET_ANTHROPIC_KEY yoki secrets.json)."
)


def error_message(exc: Exception) -> str:
    """Xatoni foydalanuvchiga tushunarli, kalitsiz xabarga aylantiradi."""
    if isinstance(exc, LLMUnavailableError):
        return _KEY_MISSING
    if isinstance(exc, LLMError):
        return "⚠️ Claude API xatosi (kalit noto'g'ri, timeout yoki kvota). Qayta urinib ko'ring."
    return "⚠️ Kutilmagan xatolik yuz berdi. Keyinroq qayta urinib ko'ring."


class CommandRouter:
    """Klient xabarlarini bajaruvchi (streaming + non-streaming)."""

    def __init__(
        self, agent: Agent, *, streaming: bool = True, observability: Observability | None = None
    ) -> None:
        self._agent = agent
        self._streaming = streaming
        self._obs = observability

    @property
    def supports_streaming(self) -> bool:
        """Streaming yoqilgan va agent buni qo'llab-quvvatlaydimi."""
        return self._streaming and isinstance(self._agent, StreamingAgent)

    async def handle(self, message: ClientMessage) -> str | None:
        """Xabarni bajaradi (non-stream); ``chat`` uchun Agent javobi yoki aniq xato matni."""
        if message.type == "chat" and message.text.strip():
            if self._obs is not None:
                self._obs.log("info", "dashboard chat buyrug'i qabul qilindi")
            try:
                return await self._agent.handle(message.text)
            except Exception as exc:
                self._log_error(exc)
                return error_message(exc)
        if message.type == "ping":
            return "pong"
        return None

    async def stream(self, message: ClientMessage) -> AsyncIterator[str]:
        """``chat`` xabarini stream qiladi — javob bo'laklari (delta); xato bo'lsa xato-matn."""
        if message.type != "chat" or not message.text.strip():
            return
        if not isinstance(self._agent, StreamingAgent):
            yield await self.handle(message) or ""
            return
        if self._obs is not None:
            self._obs.log("info", "dashboard chat (stream) qabul qilindi")
        try:
            async for delta in self._agent.stream(message.text):
                yield delta
        except Exception as exc:
            self._log_error(exc)
            yield error_message(exc)

    def _log_error(self, exc: Exception) -> None:
        if self._obs is not None:
            self._obs.log("warning", "chat javob bera olmadi", error=type(exc).__name__)
