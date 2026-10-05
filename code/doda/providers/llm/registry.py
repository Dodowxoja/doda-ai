"""``LLMRegistry`` — provayderlarni tanlash, **fallback zanjiri** va **circuit-breaker**.

Registry o'zi ham :class:`LLMProvider` (fasad): birlamchi provayderni ishlatadi, xato bo'lsa
navbatdagi zaxiraga o'tadi. Circuit-breaker: ketma-ket xato bergan provayder vaqtincha
"o'chiriladi" (cooldown), keyin qayta sinaladi — foydasiz urinishlarning oldini oladi.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable, Sequence

from code.doda.core.errors import ConfigError, LLMError, LLMUnavailableError
from code.doda.core.interfaces.llm import LLMProvider
from code.doda.core.interfaces.observability import Observability
from code.doda.core.models.llm import Capabilities, LLMRequest, LLMResponse, StreamChunk

_KNOWN_UNIMPLEMENTED = frozenset({"gemini", "openai", "ollama", "lmstudio", "openrouter"})


class _CircuitBreaker:
    """Bitta provayder uchun circuit-breaker (ketma-ket xatolarni kuzatadi)."""

    def __init__(self, threshold: int, cooldown_s: float) -> None:
        self._threshold = threshold
        self._cooldown = cooldown_s
        self._failures = 0
        self._opened_at = 0.0

    def allow(self, now: float) -> bool:
        """Hozir bu provayderni sinash mumkinmi (ochiq bo'lsa cooldown tekshiriladi)."""
        if self._failures < self._threshold:
            return True
        return (now - self._opened_at) >= self._cooldown

    def record_success(self) -> None:
        self._failures = 0

    def record_failure(self, now: float) -> None:
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = now


class LLMRegistry:
    """Bir yoki bir nechta provayder ustidan fallback + circuit-breaker beruvchi fasad."""

    def __init__(
        self,
        providers: Sequence[LLMProvider],
        *,
        observability: Observability | None = None,
        failure_threshold: int = 3,
        cooldown_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not providers:
            raise ValueError("LLMRegistry kamida bitta provayder talab qiladi")
        self._providers = list(providers)
        self._obs = observability
        self._clock = clock
        self._breakers = [_CircuitBreaker(failure_threshold, cooldown_s) for _ in self._providers]

    @property
    def name(self) -> str:
        return self._providers[0].name

    @property
    def capabilities(self) -> Capabilities:
        return self._providers[0].capabilities

    async def chat(self, request: LLMRequest) -> LLMResponse:
        last_error: LLMError | None = None
        attempted = False
        now = self._clock()
        for provider, breaker in zip(self._providers, self._breakers, strict=True):
            if not breaker.allow(now):
                continue
            attempted = True
            try:
                response = await provider.chat(request)
            except LLMError as exc:
                last_error = exc
                breaker.record_failure(now)
                self._log_fallback(provider.name, exc)
                continue
            breaker.record_success()
            return response

        if not attempted:
            raise LLMUnavailableError(
                "Barcha LLM provayderlar vaqtincha o'chirilgan (circuit open)"
            )
        raise LLMError(f"Barcha LLM provayderlar muvaffaqiyatsiz: {last_error}") from last_error

    def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        now = self._clock()
        for provider, breaker in zip(self._providers, self._breakers, strict=True):
            if breaker.allow(now):
                return provider.stream(request)
        return self._providers[0].stream(request)

    def _log_fallback(self, provider_name: str, error: LLMError) -> None:
        if self._obs is not None:
            self._obs.log(
                "warning",
                f"LLM provayder '{provider_name}' xato berdi, zaxiraga o'tyapman",
                error=repr(error),
            )


def build_llm(
    *,
    provider: str,
    model: str,
    max_tokens: int,
    api_key: str | None,
    observability: Observability,
) -> LLMProvider:
    """Config'ga qarab LLM provayderni (registry bilan o'ralgan) quradi.

    Raises:
        LLMUnavailableError: Provayder ma'lum, lekin hali qo'llab-quvvatlanmaydi (v1.1+).
        ConfigError: Provayder nomi noma'lum.
    """
    from code.doda.providers.llm.claude import ClaudeProvider

    name = provider.lower()
    if name == "claude":
        claude = ClaudeProvider(
            model=model,
            max_tokens=max_tokens,
            observability=observability,
            api_key=api_key,
        )
        return LLMRegistry([claude], observability=observability)
    if name in _KNOWN_UNIMPLEMENTED:
        raise LLMUnavailableError(f"LLM provayder '{name}' hali qo'llab-quvvatlanmaydi (v1.1+)")
    raise ConfigError(f"Noma'lum LLM provayder: '{provider}'")
