"""``Event`` modeli testlari — default, immutability, noyob trace_id."""

from __future__ import annotations

import dataclasses

import pytest

from doda.core.models.event import Event


def test_defaults() -> None:
    event = Event(name="a")
    assert event.name == "a"
    assert event.payload == {}
    assert event.source == ""
    assert isinstance(event.trace_id, str)
    assert event.trace_id != ""


def test_is_frozen() -> None:
    event = Event(name="a")
    with pytest.raises(dataclasses.FrozenInstanceError):
        event.name = "b"  # type: ignore[misc]


def test_trace_ids_are_unique() -> None:
    assert Event(name="a").trace_id != Event(name="a").trace_id


def test_payload_is_preserved() -> None:
    event = Event(name="a", payload={"k": 1}, source="test")
    assert event.payload == {"k": 1}
    assert event.source == "test"
