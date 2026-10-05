"""``SecretStore`` porti — sirlarni (API kalit, token) xavfsiz o'qish/yozish (core).

Sirlar HECH QACHON kodda/config'da/logda bo'lmaydi. Ular shu port ortida saqlanadi.
Implementatsiya ``providers/secrets/`` da (hozir env + shifrsiz fayl 0600; kelajakda OS
keychain — port o'zgarmaydi). Qarang: ``docs/SECURITY.md``.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretStore(Protocol):
    """Sirlarni saqlash/olish abstraksiyasi."""

    def get(self, key: str) -> str | None:
        """``key`` bo'yicha sirni qaytaradi yoki topilmasa ``None``."""
        ...

    def require(self, key: str) -> str:
        """``key`` bo'yicha sirni qaytaradi; yo'q bo'lsa :class:`SecretNotFoundError`.

        Raises:
            doda.core.errors.SecretNotFoundError: Sir mavjud bo'lmaganda.
        """
        ...

    def set(self, key: str, value: str) -> None:
        """Sirni saqlaydi (xavfsiz manbaga). Mavjud qiymatni almashtiradi."""
        ...
