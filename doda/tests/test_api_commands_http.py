"""``CommandRouter`` + HTTP handlerlar testi (tarmoqsiz — soxta Agent)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from doda.container import build_container
from doda.core.errors import LLMError, LLMUnavailableError
from doda.interfaces.api import http_api
from doda.interfaces.api.commands import CommandRouter
from doda.interfaces.api.protocol import ClientMessage
from doda.providers.observability import BasicObservability


class FakeAgent:
    def __init__(self) -> None:
        self.handled: list[str] = []

    async def handle(self, user_text: str) -> str:
        self.handled.append(user_text)
        return f"javob: {user_text}"


class StreamAgent(FakeAgent):
    async def stream(self, user_text: str) -> AsyncIterator[str]:
        for word in user_text.split():
            yield word + " "


class NoKeyAgent:
    async def handle(self, user_text: str) -> str:
        raise LLMUnavailableError("kalit yo'q")


class ApiErrorAgent:
    async def handle(self, user_text: str) -> str:
        raise LLMError("timeout")


class GenericErrorAgent:
    async def handle(self, user_text: str) -> str:
        raise ValueError("kutilmagan")


class StreamBoomAgent(FakeAgent):
    async def stream(self, user_text: str) -> AsyncIterator[str]:
        raise LLMError("stream uzildi")
        yield ""  # pragma: no cover


# ---------------- CommandRouter: handle ----------------


async def test_chat_routes_to_agent() -> None:
    agent = FakeAgent()
    router = CommandRouter(agent, observability=BasicObservability())
    result = await router.handle(ClientMessage(type="chat", text="salom"))
    assert result == "javob: salom"
    assert agent.handled == ["salom"]


async def test_no_key_error_message() -> None:
    result = await CommandRouter(NoKeyAgent(), observability=BasicObservability()).handle(
        ClientMessage(type="chat", text="salom")
    )
    assert result is not None
    assert "⚠️" in result and "anthropic.key" in result


async def test_api_error_message() -> None:
    result = await CommandRouter(ApiErrorAgent()).handle(ClientMessage(type="chat", text="salom"))
    assert result is not None
    assert "⚠️" in result and "Claude API xatosi" in result


async def test_generic_error_message() -> None:
    result = await CommandRouter(GenericErrorAgent()).handle(ClientMessage(type="chat", text="x"))
    assert result is not None
    assert "⚠️" in result and "Kutilmagan" in result


async def test_ping_returns_pong() -> None:
    assert await CommandRouter(FakeAgent()).handle(ClientMessage(type="ping")) == "pong"


async def test_unknown_and_empty_return_none() -> None:
    router = CommandRouter(FakeAgent())
    assert await router.handle(ClientMessage(type="unknown")) is None
    assert await router.handle(ClientMessage(type="chat", text="   ")) is None


# ---------------- CommandRouter: streaming ----------------


def test_supports_streaming() -> None:
    assert CommandRouter(StreamAgent()).supports_streaming is True
    assert CommandRouter(FakeAgent()).supports_streaming is False  # stream() yo'q
    assert CommandRouter(StreamAgent(), streaming=False).supports_streaming is False


async def test_stream_yields_deltas() -> None:
    router = CommandRouter(StreamAgent(), observability=BasicObservability())
    deltas = [d async for d in router.stream(ClientMessage(type="chat", text="salom dunyo"))]
    assert "".join(deltas).strip() == "salom dunyo"


async def test_stream_error_yields_message() -> None:
    router = CommandRouter(StreamBoomAgent(), observability=BasicObservability())
    deltas = [d async for d in router.stream(ClientMessage(type="chat", text="salom"))]
    assert any("⚠️" in d for d in deltas)


async def test_stream_non_streaming_agent_falls_back() -> None:
    deltas = [
        d async for d in CommandRouter(FakeAgent()).stream(ClientMessage(type="chat", text="hi"))
    ]
    assert deltas == ["javob: hi"]


async def test_stream_ignores_non_chat() -> None:
    deltas = [d async for d in CommandRouter(StreamAgent()).stream(ClientMessage(type="ping"))]
    assert deltas == []


# ---------------- HTTP handlers ----------------


def test_health() -> None:
    out = http_api.health()
    assert out["status"] == "ok"
    assert out["service"] == "doda"


def test_status_reads_container() -> None:
    out = http_api.status(build_container())
    assert out["service"] == "doda"
    assert "components" in out
    assert out["components"]["agent"] == "ready"


async def test_chat_handler() -> None:
    out = await http_api.chat(FakeAgent(), {"message": "salom"})
    assert out["response"] == "javob: salom"


async def test_chat_handler_empty() -> None:
    out = await http_api.chat(FakeAgent(), {})
    assert "error" in out
