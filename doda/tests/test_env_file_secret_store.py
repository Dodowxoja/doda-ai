"""``EnvFileSecretStore`` testlari — SecretStore contract + env/fayl xususiyatlari."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from doda.core.interfaces.secrets import SecretStore
from doda.providers.secrets import EnvFileSecretStore
from doda.tests.contracts.secret_store_contract import SecretStoreContract


class TestEnvFileSecretStore(SecretStoreContract):
    """EnvFileSecretStore SecretStore kelishuvini bajaradi + o'ziga xos testlar."""

    def make_store(self, tmp_path: Path) -> SecretStore:
        return EnvFileSecretStore(tmp_path / "secrets.json")

    def test_env_var_overrides_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        store = EnvFileSecretStore(tmp_path / "secrets.json")
        store.set("api.key", "from-file")
        monkeypatch.setenv("DODA_SECRET_API_KEY", "from-env")
        assert store.get("api.key") == "from-env"

    def test_file_is_owner_only(self, tmp_path: Path) -> None:
        path = tmp_path / "secrets.json"
        store = EnvFileSecretStore(path)
        store.set("k", "v")
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    def test_missing_file_reads_empty(self, tmp_path: Path) -> None:
        store = EnvFileSecretStore(tmp_path / "does-not-exist.json")
        assert store.get("k") is None

    def test_corrupt_json_reads_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "secrets.json"
        path.write_text("not valid json {{{", encoding="utf-8")
        assert EnvFileSecretStore(path).get("k") is None

    def test_non_dict_json_reads_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "secrets.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        assert EnvFileSecretStore(path).get("k") is None
