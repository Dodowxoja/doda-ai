"""``LLMVerifier`` testi — hukmni parse qilish + fail-open."""

from __future__ import annotations

from code.doda.planning import LLMVerifier
from code.doda.providers.llm import FakeLLMProvider


async def test_parses_ok_true() -> None:
    verifier = LLMVerifier(FakeLLMProvider(reply='{"ok": true, "reason": "bajarildi"}'))
    verdict = await verifier.verify("maqsad", "natija")
    assert verdict.ok is True
    assert verdict.reason == "bajarildi"


async def test_parses_ok_false() -> None:
    verifier = LLMVerifier(FakeLLMProvider(reply='{"ok": false, "reason": "kam"}'))
    verdict = await verifier.verify("maqsad", "natija")
    assert verdict.ok is False
    assert verdict.reason == "kam"


async def test_unparseable_is_fail_open() -> None:
    verifier = LLMVerifier(FakeLLMProvider(reply="JSON yo'q"))
    verdict = await verifier.verify("maqsad", "natija")
    assert verdict.ok is True
    assert "aniq emas" in verdict.reason


async def test_missing_ok_key_is_fail_open() -> None:
    verifier = LLMVerifier(FakeLLMProvider(reply='{"reason": "xato"}'))
    verdict = await verifier.verify("maqsad", "natija")
    assert verdict.ok is True
