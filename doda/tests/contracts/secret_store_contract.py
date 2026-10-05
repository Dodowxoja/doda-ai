"""``SecretStore`` porti uchun contract — har qanday implementatsiya bajarishi shart."""

from __future__ import annotations

from pathlib import Path

import pytest

from doda.core.errors import SecretNotFoundError
from doda.core.interfaces.secrets import SecretStore


class SecretStoreContract:
    """SecretStore kelishuvi (subklass ``make_store()``ni beradi)."""

    def make_store(self, tmp_path: Path) -> SecretStore:
        """Test qilinadigan bo'sh SecretStore qaytaradi (``tmp_path``dan foydalanadi)."""
        raise NotImplementedError

    def test_set_then_get_roundtrip(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        store.set("api.key", "secret-value")
        assert store.get("api.key") == "secret-value"

    def test_get_missing_returns_none(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        assert store.get("nope") is None

    def test_require_missing_raises(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        with pytest.raises(SecretNotFoundError):
            store.require("nope")

    def test_require_present_returns_value(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        store.set("token", "abc")
        assert store.require("token") == "abc"

    def test_set_overwrites(self, tmp_path: Path) -> None:
        store = self.make_store(tmp_path)
        store.set("k", "one")
        store.set("k", "two")
        assert store.get("k") == "two"
