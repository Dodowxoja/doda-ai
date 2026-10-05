"""EVALUATION qatlami — AI sifatini baholash (regressiya + metrikalar).

``EvalRunner`` holatlarni Agentga qarshi yuritadi; ``KeywordEvaluator`` (deterministik) yoki
``LLMJudge`` (LLM-as-judge) baholaydi. Natija ``EvalReport`` (o'tish-foizi, o'rtacha ball).
"""

from code.doda.evaluation.judge import LLMJudge
from code.doda.evaluation.runner import EvalRunner
from code.doda.evaluation.scorer import KeywordEvaluator

__all__ = ["EvalRunner", "KeywordEvaluator", "LLMJudge"]
