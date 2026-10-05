"""``KeywordEvaluator`` — kutilgan belgilarga qarab javobni baholaydi (deterministik).

Regressiya testlari uchun tez va LLM'siz: javobda kutilgan barcha belgilar bo'lsa — o'tdi;
ball = topilgan belgilar ulushi. Kutilgan belgi bo'lmasa, holat avtomatik o'tadi.
"""

from __future__ import annotations

from code.doda.core.models.evaluation import EvalCase, EvalResult


class KeywordEvaluator:
    """Javobda kutilgan kalit belgilar borligini tekshiradi."""

    async def evaluate(self, case: EvalCase, response: str) -> EvalResult:
        if not case.expect_contains:
            return EvalResult(case_id=case.id, passed=True, score=1.0, response=response)
        lowered = response.lower()
        matched = [token for token in case.expect_contains if token.lower() in lowered]
        missing = [token for token in case.expect_contains if token.lower() not in lowered]
        score = len(matched) / len(case.expect_contains)
        detail = "" if not missing else f"yetishmayapti: {', '.join(missing)}"
        return EvalResult(
            case_id=case.id,
            passed=not missing,
            score=score,
            response=response,
            detail=detail,
        )
