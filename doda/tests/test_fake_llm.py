"""``FakeLLMProvider`` testlari — LLMProvider contract + fake xususiyatlari."""

from __future__ import annotations

import pytest

from doda.core.errors import LLMError
from doda.core.interfaces.llm import LLMProvider
from doda.core.models.llm import LLMRequest, Message, Role
from doda.providers.llm import FakeLLMProvider
from doda.tests.contracts.llm_provider_contract import LLMProviderContract


class TestFakeLLMProvider(LLMProviderContract):
    def make_provider(self) -> LLMProvider:
        return FakeLLMProvider(reply="hello world")

    async def test_records_requests(self) -> None:
        provider = FakeLLMProvider(reply="ok")
        request = LLMRequest(messages=(Message.text(Role.USER, "hi"),))
        await provider.chat(request)
        assert provider.requests == [request]

    async def test_fail_raises_on_chat(self) -> None:
        provider = FakeLLMProvider(fail=True)
        with pytest.raises(LLMError):
            await provider.chat(LLMRequest(messages=(Message.text(Role.USER, "hi"),)))
