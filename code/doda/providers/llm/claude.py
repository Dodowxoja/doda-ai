"""``ClaudeProvider`` — Anthropic Claude uchun LLMProvider implementatsiyasi.

Anthropic SDK murakkab turlarga ega, shuning uchun u **``Any`` chegarasida** ishlatiladi
(tashqi bog'liqlik izolyatsiyasi); bizning barcha mantiq (mapping) sof va tiplangan.
Token sarfi Observability metrikasiga yoziladi (M14 Telemetry uchun hook).

Klient DI orqali beriladi (test uchun soxta klient) YOKI ``api_key``dan lazy quriladi.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from code.doda.core.errors import LLMError, LLMUnavailableError
from code.doda.core.interfaces.observability import Observability
from code.doda.core.models.llm import Capabilities, LLMRequest, LLMResponse, StreamChunk
from code.doda.providers.llm.mapping import from_anthropic_response, to_anthropic_params

_CAPABILITIES = Capabilities(streaming=True, tools=True, vision=True)


class ClaudeProvider:
    """Anthropic Claude LLMProvider."""

    def __init__(
        self,
        *,
        model: str,
        max_tokens: int,
        observability: Observability,
        client: Any = None,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._obs = observability
        self._client: Any = client
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "claude"

    @property
    def capabilities(self) -> Capabilities:
        return _CAPABILITIES

    def _get_client(self) -> Any:
        """Anthropic klientini qaytaradi (lazy quradi; kalit yo'q bo'lsa xato)."""
        if self._client is None:
            if not self._api_key:
                raise LLMUnavailableError("Claude API kaliti yo'q (SecretStore'ga qo'ying)")
            try:
                from anthropic import AsyncAnthropic
            except ImportError as exc:  # pragma: no cover
                raise LLMUnavailableError("anthropic kutubxonasi o'rnatilmagan") from exc
            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    async def chat(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()
        params = to_anthropic_params(request, self._model, self._max_tokens)
        try:
            with self._obs.span("llm.claude.chat"):
                raw = await client.messages.create(**params)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"Claude chat xatosi: {exc}") from exc
        response = from_anthropic_response(raw)
        self._record_usage(response)
        return response

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        client = self._get_client()
        params = to_anthropic_params(request, self._model, self._max_tokens)
        async with client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield StreamChunk(delta=str(text))

    def _record_usage(self, response: LLMResponse) -> None:
        """Token sarfini metrikaga yozadi (xarajat/telemetriya)."""
        self._obs.metric("llm.tokens.input", float(response.usage.input_tokens), provider="claude")
        self._obs.metric(
            "llm.tokens.output", float(response.usage.output_tokens), provider="claude"
        )
        self._obs.metric("llm.calls", 1.0, provider="claude")
