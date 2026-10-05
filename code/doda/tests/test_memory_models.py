"""Xotira modellari testlari."""

from __future__ import annotations

import dataclasses

import pytest

from code.doda.core.models.memory import MemoryItem, MemoryType


def test_create_generates_id_and_defaults() -> None:
    item = MemoryItem.create("salom", MemoryType.FACT)
    assert item.id != ""
    assert item.content == "salom"
    assert item.type is MemoryType.FACT
    assert item.user_id == "owner"
    assert item.valid is True


def test_create_unique_ids() -> None:
    a = MemoryItem.create("x", MemoryType.FACT)
    b = MemoryItem.create("x", MemoryType.FACT)
    assert a.id != b.id


def test_is_frozen() -> None:
    item = MemoryItem.create("x", MemoryType.FACT)
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.content = "y"  # type: ignore[misc]
