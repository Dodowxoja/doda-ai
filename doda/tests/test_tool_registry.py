"""``ToolRegistry`` testlari — ro'yxat, specs, dispatch, xato-izolyatsiya."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import pytest

from doda.core.models.llm import ToolCall
from doda.providers.observability import BasicObservability
from doda.tools import ToolRegistry


class _EchoTool:
    def __init__(self, name: str = "echo") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "aks-sado"

    @property
    def parameters(self) -> Mapping[str, Any]:
        return {"type": "object", "properties": {}}

    async def run(self, arguments: Mapping[str, Any]) -> str:
        return f"echo:{arguments.get('text', '')}"


class _BoomTool(_EchoTool):
    async def run(self, arguments: Mapping[str, Any]) -> str:
        raise RuntimeError("portladi")


def test_register_duplicate_raises() -> None:
    registry = ToolRegistry([_EchoTool()])
    with pytest.raises(ValueError, match="allaqachon"):
        registry.register(_EchoTool())


def test_specs_reflect_registered_tools() -> None:
    registry = ToolRegistry([_EchoTool("a"), _EchoTool("b")])
    names = {spec.name for spec in registry.specs()}
    assert names == {"a", "b"}


async def test_execute_dispatches_by_name() -> None:
    registry = ToolRegistry([_EchoTool()])
    result = await registry.execute(ToolCall(id="1", name="echo", arguments={"text": "salom"}))
    assert result == "echo:salom"


async def test_execute_unknown_tool_returns_error() -> None:
    registry = ToolRegistry([_EchoTool()])
    result = await registry.execute(ToolCall(id="1", name="yoq", arguments={}))
    assert "noma'lum asbob" in result


async def test_execute_isolates_and_logs_tool_error(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("doda.test.tools")
    registry = ToolRegistry([_BoomTool()], observability=BasicObservability(logger=logger))
    with caplog.at_level(logging.WARNING, logger="doda.test.tools"):
        result = await registry.execute(ToolCall(id="1", name="echo", arguments={}))
    assert "xato" in result
    assert "portladi" in result
    assert any("echo" in record.message for record in caplog.records)
