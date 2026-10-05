"""JSON-ajratish yordamchilari testi (``parsing.py``)."""

from __future__ import annotations

from doda.planning.parsing import extract_json_array, extract_json_object


def test_array_plain() -> None:
    assert extract_json_array('["a", "b"]') == ["a", "b"]


def test_array_surrounded_by_text() -> None:
    assert extract_json_array('Mana reja: ["a", "b"] tayyor') == ["a", "b"]


def test_array_no_brackets_returns_none() -> None:
    assert extract_json_array("hech qanday massiv yo'q") is None
    assert extract_json_array("[buzuq") is None  # yopuvchi qavs yo'q


def test_array_malformed_json_returns_none() -> None:
    assert extract_json_array("[1 2 3]") is None  # qavs bor, lekin JSON buzuq


def test_object_plain() -> None:
    assert extract_json_object('{"ok": true}') == {"ok": True}


def test_object_surrounded_by_text() -> None:
    assert extract_json_object('Javob: {"ok": false, "reason": "x"}!') == {
        "ok": False,
        "reason": "x",
    }


def test_object_no_braces_returns_none() -> None:
    assert extract_json_object("obyekt yo'q") is None
    assert extract_json_object("{buzuq") is None  # yopuvchi qavs yo'q


def test_object_malformed_json_returns_none() -> None:
    assert extract_json_object("{ok true}") is None  # qavs bor, lekin JSON buzuq
