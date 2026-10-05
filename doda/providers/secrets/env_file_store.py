"""``EnvFileSecretStore`` — SecretStore portining env + lokal fayl implementatsiyasi.

Sirni izlash tartibi: **muhit-o'zgaruvchi** (``DODA_SECRET_<KEY>``) → **lokal fayl**
(``<data_dir>/secrets.json``, ruxsat ``0600``). Yozish faylga boradi.

Bu Foundation uchun yetarli va xavfsiz (fayl faqat foydalanuvchiniki). Desktop bosqichida
bu OS **keychain** (Keychain/Credential Manager/Secret Service) bilan almashtiriladi —
port o'zgarmaydi. Qarang: ``docs/SECURITY.md``.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from doda.core.errors import SecretNotFoundError

_ENV_PREFIX = "DODA_SECRET_"


def _env_name(key: str) -> str:
    """Sir kalitini muhit-o'zgaruvchi nomiga aylantiradi (``api.key`` → ``DODA_SECRET_API_KEY``)."""
    return _ENV_PREFIX + key.upper().replace(".", "_").replace("-", "_")


class EnvFileSecretStore:
    """Env + lokal shifrsiz fayl asosidagi sir-saqlagich."""

    def __init__(self, file_path: Path) -> None:
        """
        Args:
            file_path: Sirlar saqlanadigan JSON fayl yo'li (``0600`` ruxsat bilan yoziladi).
        """
        self._file = file_path

    def get(self, key: str) -> str | None:
        """Sirni env yoki fayldan qaytaradi; topilmasa ``None``."""
        env_value = os.environ.get(_env_name(key))
        if env_value:
            return env_value
        return self._read_file().get(key)

    def require(self, key: str) -> str:
        """Sirni qaytaradi; yo'q bo'lsa :class:`SecretNotFoundError`."""
        value = self.get(key)
        if value is None:
            raise SecretNotFoundError(f"Sir topilmadi: '{key}'")
        return value

    def set(self, key: str, value: str) -> None:
        """Sirni faylga yozadi (fayl ``0600`` ruxsat bilan yaratiladi/yangilanadi)."""
        data = self._read_file()
        data[key] = value
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._file.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0600

    def _read_file(self) -> dict[str, str]:
        """Sirlar faylini o'qiydi (yo'q/buzuq bo'lsa bo'sh lug'at)."""
        try:
            raw = self._file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(parsed, dict):
            return {}
        return {str(k): str(v) for k, v in parsed.items()}
