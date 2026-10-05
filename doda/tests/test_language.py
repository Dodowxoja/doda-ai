"""``detect_language`` testi — uz default, ru/en aniqlash."""

from __future__ import annotations

from doda.voice.language import detect_language


def test_detects_russian_by_cyrillic() -> None:
    assert detect_language("привет как дела") == "ru"


def test_detects_english_by_markers() -> None:
    assert detect_language("hello what can you help") == "en"


def test_detects_uzbek_by_markers() -> None:
    assert detect_language("salom menga yordam kerak") == "uz"


def test_defaults_to_uz_when_unknown() -> None:
    assert detect_language("xyz qwerty") == "uz"


def test_custom_default() -> None:
    assert detect_language("zzz", default="en") == "en"
