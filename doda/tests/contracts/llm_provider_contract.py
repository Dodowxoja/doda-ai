"""``LLMProvider`` porti uchun contract — har qanday provayder bajarishi shart.

Yangi provayder (Fake, Claude, kelajakda Gemini/OpenAI) shu klassni meros olib
``make_provider()``ni beradi — barcha kelishuv testlari avtomatik ishlaydi.
"""

from __future__ import annotations

from doda.core.interfaces.llm import LLMProvider
from doda.core.models.llm import Capabilities, LLMRequest, LLMResponse, Message, Role


class LLMProviderContract:
    """LLMProvider kelishuvi (subklass ``make_provider()``ni beradi)."""

    def make_provider(self) -> LLMProvider:
        """Bo'sh (matnli javob beradigan) provayder qaytaradi."""
        raise NotImplementedError

    def make_request(self) -> LLMRequest:
        return LLMRequest(messages=(Message.text(Role.USER, "salom"),))

    def test_name_is_nonempty(self) -> None:
        assert self.make_provider().name != ""

    def test_capabilities_is_capabilities(self) -> None:
        assert isinstance(self.make_provider().capabilities, Capabilities)

    async def test_chat_returns_text_response(self) -> None:
        response = await self.make_provider().chat(self.make_request())
        assert isinstance(response, LLMResponse)
        assert response.text != ""

    async def test_stream_yields_nonempty_text(self) -> None:
        provider = self.make_provider()
        if not provider.capabilities.streaming:
            return
        chunks = [chunk.delta async for chunk in provider.stream(self.make_request())]
        assert "".join(chunks) != ""
