"""``LLMRegistry`` va ``build_llm`` testlari — fallback, circuit-breaker, factory."""

from __future__ import annotations

import pytest

from doda.core.errors import ConfigError, LLMError, LLMUnavailableError
from doda.core.models.llm import LLMRequest, Message, Role
from doda.providers.llm import FakeLLMProvider, LLMRegistry, build_llm
from doda.providers.observability import BasicObservability


def _request() -> LLMRequest:
    return LLMRequest(messages=(Message.text(Role.USER, "hi"),))


async def test_single_provider_returns_response() -> None:
    registry = LLMRegistry([FakeLLMProvider(reply="ok")])
    assert (await registry.chat(_request())).text == "ok"


async def test_fallback_on_primary_failure() -> None:
    registry = LLMRegistry(
        [FakeLLMProvider(name="a", fail=True), FakeLLMProvider(name="b", reply="ok")]
    )
    assert (await registry.chat(_request())).text == "ok"


async def test_all_providers_fail_raises() -> None:
    registry = LLMRegistry([FakeLLMProvider(fail=True), FakeLLMProvider(fail=True)])
    with pytest.raises(LLMError):
        await registry.chat(_request())


def test_empty_registry_raises() -> None:
    with pytest.raises(ValueError):
        LLMRegistry([])


async def test_circuit_opens_and_skips_provider() -> None:
    now = [0.0]
    primary = FakeLLMProvider(name="p", fail=True)
    backup = FakeLLMProvider(name="b", reply="ok")
    registry = LLMRegistry(
        [primary, backup], failure_threshold=2, cooldown_s=100.0, clock=lambda: now[0]
    )
    await registry.chat(_request())
    await registry.chat(_request())  # 2-xato -> circuit ochiladi
    calls = len(primary.requests)
    await registry.chat(_request())  # primary ochiq -> sinovga urinilmaydi
    assert len(primary.requests) == calls


async def test_circuit_recovers_after_cooldown() -> None:
    now = [0.0]
    primary = FakeLLMProvider(name="p", fail=True)
    backup = FakeLLMProvider(name="b", reply="ok")
    registry = LLMRegistry(
        [primary, backup], failure_threshold=1, cooldown_s=50.0, clock=lambda: now[0]
    )
    await registry.chat(_request())  # 1-xato -> ochiladi (threshold=1)
    before = len(primary.requests)
    now[0] = 100.0  # cooldown o'tdi
    await registry.chat(_request())  # primary qayta sinaladi
    assert len(primary.requests) == before + 1


async def test_name_and_capabilities_from_primary() -> None:
    registry = LLMRegistry([FakeLLMProvider(name="primary")])
    assert registry.name == "primary"
    assert registry.capabilities.streaming is True


async def test_stream_delegates_to_provider() -> None:
    registry = LLMRegistry([FakeLLMProvider(reply="ha yoq")])
    chunks = [chunk.delta async for chunk in registry.stream(_request())]
    assert "".join(chunks).strip() != ""


async def test_all_circuits_open_raises_unavailable() -> None:
    now = [0.0]
    registry = LLMRegistry(
        [FakeLLMProvider(fail=True)], failure_threshold=1, cooldown_s=1000.0, clock=lambda: now[0]
    )
    with pytest.raises(LLMError):  # 1-chat: oddiy xato (urinildi)
        await registry.chat(_request())
    with pytest.raises(LLMUnavailableError):  # 2-chat: circuit ochiq, urinilmaydi
        await registry.chat(_request())


async def test_fallback_logs_when_observability_present() -> None:
    registry = LLMRegistry(
        [FakeLLMProvider(name="a", fail=True), FakeLLMProvider(reply="ok")],
        observability=BasicObservability(),
    )
    assert (await registry.chat(_request())).text == "ok"


def test_build_llm_claude_returns_registry() -> None:
    provider = build_llm(
        provider="claude", model="m", max_tokens=1, api_key=None, observability=BasicObservability()
    )
    assert isinstance(provider, LLMRegistry)


def test_build_llm_unimplemented_raises() -> None:
    with pytest.raises(LLMUnavailableError):
        build_llm(
            provider="gemini",
            model="m",
            max_tokens=1,
            api_key=None,
            observability=BasicObservability(),
        )


def test_build_llm_unknown_raises() -> None:
    with pytest.raises(ConfigError):
        build_llm(
            provider="xyz",
            model="m",
            max_tokens=1,
            api_key=None,
            observability=BasicObservability(),
        )
