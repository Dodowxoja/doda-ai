"""LLM domen modellari testlari."""

from __future__ import annotations

import dataclasses

import pytest

from doda.core.models.llm import (
    Capabilities,
    LLMResponse,
    Message,
    Role,
    TextContent,
    Usage,
)


def test_message_text_helper() -> None:
    message = Message.text(Role.USER, "salom")
    assert message.role is Role.USER
    assert message.content == (TextContent("salom"),)


def test_role_is_str_enum() -> None:
    assert Role.USER.value == "user"


def test_llm_response_defaults() -> None:
    response = LLMResponse(text="ok")
    assert response.text == "ok"
    assert response.tool_calls == ()
    assert response.usage == Usage()
    assert response.model == ""


def test_models_are_frozen() -> None:
    capabilities = Capabilities(streaming=True)
    with pytest.raises(dataclasses.FrozenInstanceError):
        capabilities.streaming = False  # type: ignore[misc]
