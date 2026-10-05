"""``Conversation`` testlari."""

from __future__ import annotations

import pytest

from doda.agent import Conversation
from doda.core.models.llm import Message, Role, TextContent


def _message(text: str) -> Message:
    return Message.text(Role.USER, text)


def test_add_and_messages() -> None:
    conversation = Conversation()
    conversation.add(_message("a"))
    conversation.add(_message("b"))
    assert len(conversation.messages()) == 2


def test_window_drops_oldest() -> None:
    conversation = Conversation(max_messages=2)
    for text in ("a", "b", "c"):
        conversation.add(_message(text))
    messages = conversation.messages()
    assert len(messages) == 2
    last = messages[-1].content[0]
    assert isinstance(last, TextContent)
    assert last.text == "c"


def test_clear() -> None:
    conversation = Conversation()
    conversation.add(_message("a"))
    conversation.clear()
    assert conversation.messages() == ()


def test_invalid_max_raises() -> None:
    with pytest.raises(ValueError):
        Conversation(0)
