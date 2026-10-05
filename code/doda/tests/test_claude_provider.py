"""``ClaudeProvider`` testlari — soxta Anthropic klient bilan (tarmoqsiz).

LLMProvider contract'ini bajaradi + Claude'ga xos: tool-chaqiruv parslash, token
metrikasi, kalit yo'qligida xato.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

import pytest

from code.doda.core.errors import LLMError, LLMUnavailableError
from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.models.llm import LLMRequest, Message, Role
from code.doda.providers.llm import ClaudeProvider
from code.doda.providers.observability import BasicObservability
from code.doda.tests.contracts.llm_provider_contract import LLMProviderContract


class _Usage:
    def __init__(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class _TextBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _ToolBlock:
    def __init__(self, block_id: str, name: str, arguments: dict[str, Any]) -> None:
        self.type = "tool_use"
        self.id = block_id
        self.name = name
        self.input = arguments


class _Response:
    def __init__(self, content: list[Any], usage: _Usage) -> None:
        self.content = content
        self.usage = usage
        self.stop_reason = "end_turn"
        self.model = "claude-test"


async def _aiter(items: Sequence[str]) -> AsyncIterator[str]:
    for item in items:
        yield item


class _StreamCtx:
    def __init__(self, texts: Sequence[str]) -> None:
        self._texts = texts

    async def __aenter__(self) -> _StreamCtx:
        return self

    async def __aexit__(self, *args: object) -> bool:
        return False

    @property
    def text_stream(self) -> AsyncIterator[str]:
        return _aiter(self._texts)


class _Messages:
    def __init__(self, response: _Response, texts: Sequence[str]) -> None:
        self._response = response
        self._texts = texts

    async def create(self, **kwargs: Any) -> _Response:
        return self._response

    def stream(self, **kwargs: Any) -> _StreamCtx:
        return _StreamCtx(self._texts)


class _Client:
    def __init__(self, response: _Response, texts: Sequence[str]) -> None:
        self.messages = _Messages(response, texts)


def _client(
    *,
    content: list[Any] | None = None,
    usage: _Usage | None = None,
    texts: Sequence[str] = ("ja", "vob"),
) -> _Client:
    response = _Response(
        content=content if content is not None else [_TextBlock("javob")],
        usage=usage or _Usage(10, 5),
    )
    return _Client(response, texts)


def _provider(client: _Client, observability: BasicObservability | None = None) -> ClaudeProvider:
    return ClaudeProvider(
        model="m",
        max_tokens=100,
        observability=observability or BasicObservability(),
        client=client,
    )


class TestClaudeProvider(LLMProviderContract):
    def make_provider(self) -> LLMProvider:
        return _provider(_client())


def _request() -> LLMRequest:
    return LLMRequest(messages=(Message.text(Role.USER, "salom"),))


async def test_parses_tool_calls() -> None:
    client = _client(content=[_ToolBlock("t1", "calc", {"x": 1})])
    response = await _provider(client).chat(_request())
    assert response.tool_calls[0].name == "calc"
    assert response.tool_calls[0].arguments == {"x": 1}


async def test_records_token_metrics() -> None:
    observability = BasicObservability()
    await _provider(_client(usage=_Usage(10, 5)), observability).chat(_request())
    snapshot = observability.snapshot()
    assert snapshot["llm.tokens.input{provider=claude}"] == 10.0
    assert snapshot["llm.tokens.output{provider=claude}"] == 5.0
    assert snapshot["llm.calls{provider=claude}"] == 1.0


async def test_no_client_no_key_raises() -> None:
    provider = ClaudeProvider(model="m", max_tokens=1, observability=BasicObservability())
    with pytest.raises(LLMUnavailableError):
        await provider.chat(_request())


class _FailMessages:
    async def create(self, **kwargs: Any) -> Any:
        raise RuntimeError("api ishlamayapti")


class _FailClient:
    def __init__(self) -> None:
        self.messages = _FailMessages()


async def test_chat_wraps_client_error() -> None:
    provider = ClaudeProvider(
        model="m", max_tokens=1, observability=BasicObservability(), client=_FailClient()
    )
    with pytest.raises(LLMError):
        await provider.chat(_request())
