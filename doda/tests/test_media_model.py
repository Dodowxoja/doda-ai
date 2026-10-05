"""``MediaFrame`` modeli testi."""

from __future__ import annotations

import dataclasses

import pytest

from doda.core.models.media import MediaFrame


def test_fields() -> None:
    frame = MediaFrame(media_type="image/png", data=b"xyz", source="screen")
    assert frame.media_type == "image/png"
    assert frame.data == b"xyz"
    assert frame.source == "screen"


def test_is_frozen() -> None:
    frame = MediaFrame(media_type="image/png", data=b"x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        frame.source = "y"  # type: ignore[misc]
