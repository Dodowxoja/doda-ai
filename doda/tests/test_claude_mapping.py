"""Anthropic mapping testlari (sof funksiyalar — tarmoqsiz)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from doda.core.models.llm import (
    ImageContent,
    LLMRequest,
    Message,
    Role,
    ToolResultContent,
    ToolSpec,
)
from doda.providers.llm.mapping import from_anthropic_response, to_anthropic_params


def test_system_role_goes_to_system_param() -> None:
    request = LLMRequest(
        messages=(Message.text(Role.SYSTEM, "sen DODA"), Message.text(Role.USER, "salom")),
    )
    params = to_anthropic_params(request, "model-x", 500)
    assert params["system"] == "sen DODA"
    assert len(params["messages"]) == 1
    assert params["messages"][0]["role"] == "user"


def test_request_system_field_included() -> None:
    request = LLMRequest(messages=(Message.text(Role.USER, "hi"),), system="qoida")
    params = to_anthropic_params(request, "m", 100)
    assert params["system"] == "qoida"


def test_max_tokens_default_and_override() -> None:
    base = LLMRequest(messages=(Message.text(Role.USER, "hi"),))
    assert to_anthropic_params(base, "m", 128)["max_tokens"] == 128
    override = LLMRequest(messages=(Message.text(Role.USER, "hi"),), max_tokens=42)
    assert to_anthropic_params(override, "m", 128)["max_tokens"] == 42


def test_image_content_maps() -> None:
    message = Message(role=Role.USER, content=(ImageContent("image/jpeg", "BASE64"),))
    params = to_anthropic_params(LLMRequest(messages=(message,)), "m", 100)
    block = params["messages"][0]["content"][0]
    assert block["type"] == "image"
    assert block["source"]["media_type"] == "image/jpeg"


def test_tool_result_content_maps() -> None:
    message = Message(role=Role.TOOL, content=(ToolResultContent("t1", "natija"),))
    params = to_anthropic_params(LLMRequest(messages=(message,)), "m", 100)
    block = params["messages"][0]["content"][0]
    assert block["type"] == "tool_result"
    assert block["tool_use_id"] == "t1"
    assert block["content"] == "natija"


def test_tools_mapped() -> None:
    tool = ToolSpec(name="calc", description="hisob", parameters={"type": "object"})
    params = to_anthropic_params(
        LLMRequest(messages=(Message.text(Role.USER, "x"),), tools=(tool,)), "m", 100
    )
    assert params["tools"][0]["name"] == "calc"
    assert params["tools"][0]["input_schema"] == {"type": "object"}


@dataclass
class _Usage:
    input_tokens: int = 7
    output_tokens: int = 3


@dataclass
class _TextBlock:
    text: str
    type: str = "text"


@dataclass
class _ToolBlock:
    id: str
    name: str
    input: dict[str, Any]
    type: str = "tool_use"


@dataclass
class _Response:
    content: list[Any]
    usage: _Usage = field(default_factory=_Usage)
    stop_reason: str = "end_turn"
    model: str = "claude-test"


def test_from_response_parses_text_and_tool_calls() -> None:
    response = _Response(
        content=[_TextBlock(text="javob"), _ToolBlock(id="t1", name="calc", input={"x": 1})],
    )
    result = from_anthropic_response(response)
    assert result.text == "javob"
    assert result.tool_calls[0].name == "calc"
    assert result.tool_calls[0].arguments == {"x": 1}
    assert result.usage.input_tokens == 7
    assert result.stop_reason == "end_turn"
    assert result.model == "claude-test"
