"""``Persona`` testlari."""

from __future__ import annotations

from code.doda.core.models.memory import MemoryItem, MemoryType
from code.doda.core.models.persona import Persona


def test_render_includes_identity() -> None:
    assert "DODA" in Persona().render()


def test_render_includes_profile_and_memories() -> None:
    profile = [MemoryItem.create("Flutter yoqtiradi", MemoryType.PREFERENCE)]
    memories = [MemoryItem.create("Loyiha X ustida ishlayapti", MemoryType.PROJECT)]
    rendered = Persona().render(memories, profile)
    assert "Flutter yoqtiradi" in rendered
    assert "Loyiha X" in rendered


def test_empty_context_is_just_identity() -> None:
    persona = Persona()
    assert persona.render() == persona.identity


def test_versioned() -> None:
    assert Persona(version="2.0").version == "2.0"
