"""``FakeLLMProvider`` — deterministik, tarmoqsiz test-provayderi.

Registry/agent testlari va kelajakdagi rivojlanish uchun (real API'siz). Sozlanadigan javob,
imkoniyatlar, tool-chaqiruvlar va (fallback testi uchun) ataylab xato berish rejimi.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from code.doda.core.errors import LLMError
from code.doda.core.models.llm import (
    Capabilities,
    LLMRequest,
    LLMResponse,
    StreamChunk,
    ToolCall,
    Usage,
)


class FakeLLMProvider:
    """LLMProvider portining deterministik implementatsiyasi (test uchun)."""

    def __init__(
        self,
        *,
        name: str = "fake",
        reply: str = "ok",
        capabilities: Capabilities | None = None,
        tool_calls: Sequence[ToolCall] = (),
        fail: bool = False,
        responses: Sequence[LLMResponse] | None = None,
    ) -> None:
        self._name = name
        self._reply = reply
        self._caps = capabilities or Capabilities(streaming=True, tools=True, vision=True)
        self._tool_calls = tuple(tool_calls)
        self._fail = fail
        self._responses = list(responses) if responses is not None else None
        self._call_index = 0
        self.requests: list[LLMRequest] = []

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> Capabilities:
        return self._caps

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        if self._fail:
            raise LLMError(f"{self._name} ataylab xato berdi")
        if self._responses is not None:
            index = min(self._call_index, len(self._responses) - 1)
            self._call_index += 1
            return self._responses[index]
        return LLMResponse(
            text=self._reply,
            tool_calls=self._tool_calls,
            usage=Usage(input_tokens=1, output_tokens=1),
            model=self._name,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        self.requests.append(request)
        if self._fail:
            raise LLMError(f"{self._name} ataylab xato berdi")
        for word in self._reply.split():
            yield StreamChunk(delta=word + " ")
