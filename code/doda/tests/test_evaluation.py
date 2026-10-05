"""AI baholash testlari — model + KeywordEvaluator + LLMJudge + EvalRunner."""

from __future__ import annotations

from code.doda.core.models.evaluation import EvalCase, EvalReport, EvalResult
from code.doda.core.models.event import Event
from code.doda.evaluation import EvalRunner, KeywordEvaluator, LLMJudge
from code.doda.providers.bus import AsyncioEventBus
from code.doda.providers.llm import FakeLLMProvider
from code.doda.providers.observability import BasicObservability


class ScriptedAgent:
    """Berilgan javoblarni navbat bilan qaytaradigan soxta agent."""

    def __init__(self, *replies: str) -> None:
        self._replies = list(replies)
        self._i = 0

    async def handle(self, user_text: str) -> str:
        reply = self._replies[min(self._i, len(self._replies) - 1)]
        self._i += 1
        return reply


# ---------------- EvalReport ----------------


def test_report_aggregates() -> None:
    report = EvalReport(
        results=(
            EvalResult(case_id="a", passed=True, score=1.0, response="x"),
            EvalResult(case_id="b", passed=False, score=0.5, response="y"),
        )
    )
    assert report.total == 2
    assert report.passed_count == 1
    assert report.pass_rate == 0.5
    assert report.mean_score == 0.75


def test_empty_report() -> None:
    report = EvalReport()
    assert report.pass_rate == 0.0
    assert report.mean_score == 0.0


# ---------------- KeywordEvaluator ----------------


async def test_keyword_all_present_passes() -> None:
    evaluator = KeywordEvaluator()
    case = EvalCase(id="a", prompt="poytaxt?", expect_contains=("Toshkent",))
    result = await evaluator.evaluate(case, "Poytaxt Toshkent shahri")
    assert result.passed is True
    assert result.score == 1.0


async def test_keyword_partial_fails_with_detail() -> None:
    evaluator = KeywordEvaluator()
    case = EvalCase(id="a", prompt="?", expect_contains=("Toshkent", "Samarqand"))
    result = await evaluator.evaluate(case, "Toshkent haqida")
    assert result.passed is False
    assert result.score == 0.5
    assert "Samarqand" in result.detail


async def test_keyword_no_expectation_passes() -> None:
    result = await KeywordEvaluator().evaluate(EvalCase(id="a", prompt="?"), "har qanday javob")
    assert result.passed is True
    assert result.score == 1.0


# ---------------- LLMJudge ----------------


async def test_judge_parses_verdict() -> None:
    judge = LLMJudge(FakeLLMProvider(reply='{"passed": true, "score": 0.9, "reason": "yaxshi"}'))
    result = await judge.evaluate(EvalCase(id="a", prompt="?"), "javob")
    assert result.passed is True
    assert result.score == 0.9
    assert result.detail == "yaxshi"


async def test_judge_unparseable_fails() -> None:
    judge = LLMJudge(FakeLLMProvider(reply="JSON yo'q"))
    result = await judge.evaluate(EvalCase(id="a", prompt="?"), "javob")
    assert result.passed is False
    assert result.score == 0.0
    assert "o'qib bo'lmadi" in result.detail


# ---------------- EvalRunner ----------------


async def test_runner_reports_pass_rate() -> None:
    agent = ScriptedAgent("Toshkent", "noto'g'ri")
    cases = [
        EvalCase(id="1", prompt="poytaxt?", expect_contains=("Toshkent",)),
        EvalCase(id="2", prompt="?", expect_contains=("Samarqand",)),
    ]
    runner = EvalRunner(agent, KeywordEvaluator(), observability=BasicObservability())
    report = await runner.run(cases, label="regressiya")
    assert report.total == 2
    assert report.pass_rate == 0.5


async def test_runner_emits_completed_event() -> None:
    events = AsyncioEventBus()
    seen: list[float] = []

    async def handler(event: Event) -> None:
        seen.append(event.payload["pass_rate"])

    events.subscribe("eval.completed", handler)
    runner = EvalRunner(ScriptedAgent("Toshkent"), KeywordEvaluator(), events=events)
    await runner.run([EvalCase(id="1", prompt="?", expect_contains=("Toshkent",))], label="smoke")
    assert seen == [1.0]
