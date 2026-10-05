"""Delivery protokoli testi — encode / parse / engine→dashboard translate."""

from __future__ import annotations

import json

from doda.core.models.event import Event
from doda.interfaces.api.protocol import encode, parse_client_message, translate


def test_encode_json() -> None:
    out = json.loads(encode("voice.state", {"to": "listening"}))
    assert out == {"event": "voice.state", "data": {"to": "listening"}}


def test_encode_non_serializable_falls_back_to_str() -> None:
    out = json.loads(encode("x", {"t": object()}))
    assert isinstance(out["data"]["t"], str)


def test_parse_valid() -> None:
    msg = parse_client_message('{"type":"chat","text":"salom"}')
    assert msg is not None
    assert msg.type == "chat"
    assert msg.text == "salom"


def test_parse_invalid_returns_none() -> None:
    assert parse_client_message("buzuq{") is None
    assert parse_client_message('{"no":"type"}') is None
    assert parse_client_message('["not","object"]') is None


def test_parse_non_dict_data_ignored() -> None:
    msg = parse_client_message('{"type":"chat","data":"notdict"}')
    assert msg is not None
    assert msg.data == {}


def _ev(name: str, payload: dict[str, object]) -> Event:
    return Event(name=name, payload=payload, source="test")


def test_translate_thinking_step() -> None:
    out = translate(_ev("thinking.step", {"step": "Xotirani izlayapman"}))
    assert out[0]["event"] == "agent.thinking"
    assert out[0]["data"]["msg"] == "Xotirani izlayapman"


def test_translate_user_message() -> None:
    out = translate(_ev("message.created", {"role": "user", "text": "salom"}))
    assert out[0]["event"] == "agent.thinking"


def test_translate_assistant_message_is_raw() -> None:
    # assistant message → user-mapping shart emas → xom passthrough
    out = translate(_ev("message.created", {"role": "assistant", "text": "javob"}))
    assert out[0]["event"] == "message.created"


def test_translate_tool_called() -> None:
    out = translate(_ev("tool.called", {"name": "run_shell"}))
    names = [m["event"] for m in out]
    assert "agent.tool_started" in names
    assert "agent.thinking" in names
    assert "module.status" in names
    ms = next(m for m in out if m["event"] == "module.status")["data"]
    assert ms == {"module": "tools", "status": "active", "activity": "run_shell"}


def test_translate_tool_result() -> None:
    out = translate(_ev("tool.result", {"name": "run_shell"}))
    assert any(m["event"] == "agent.tool_completed" for m in out)
    ms = next(m for m in out if m["event"] == "module.status")["data"]
    assert ms["status"] == "idle"


def test_translate_memory_saved() -> None:
    out = translate(_ev("memory.saved", {}))
    assert out[0]["event"] == "agent.thinking"
    assert "saqlandi" in out[0]["data"]["msg"]


def test_translate_unknown_passthrough_no_module() -> None:
    out = translate(_ev("daemon.tick", {"x": 1}))
    assert len(out) == 1
    assert out[0]["event"] == "daemon.tick"
    assert out[0]["data"]["x"] == 1
    assert out[0]["data"]["_source"] == "test"
