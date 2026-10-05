"""``BasicObservability`` testlari — log / metrika / span."""

from __future__ import annotations

import pytest

from doda.providers.observability import BasicObservability


def test_log_without_fields(caplog: pytest.LogCaptureFixture) -> None:
    observability = BasicObservability()
    with caplog.at_level("INFO", logger="doda"):
        observability.log("info", "plain message")
    assert any("plain message" in record.getMessage() for record in caplog.records)


def test_metric_accumulates() -> None:
    observability = BasicObservability()
    observability.metric("hits")
    observability.metric("hits")
    observability.metric("tokens", 5.0, provider="claude")

    snapshot = observability.snapshot()
    assert snapshot["hits"] == 2.0
    assert snapshot["tokens{provider=claude}"] == 5.0


def test_snapshot_is_a_copy() -> None:
    observability = BasicObservability()
    observability.metric("a")
    snapshot = observability.snapshot()
    snapshot["a"] = 999.0
    assert observability.snapshot()["a"] == 1.0


def test_span_yields_given_trace_id_and_measures() -> None:
    observability = BasicObservability()
    with observability.span("work", trace_id="abc") as trace_id:
        assert trace_id == "abc"
    assert any(key.startswith("span.work.ms") for key in observability.snapshot())


def test_span_generates_trace_id_when_absent() -> None:
    observability = BasicObservability()
    with observability.span("work") as trace_id:
        assert isinstance(trace_id, str)
        assert trace_id != ""
