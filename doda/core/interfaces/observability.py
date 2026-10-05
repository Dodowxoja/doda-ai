"""``Observability`` porti — logging / metrics / tracing (core, implementatsiyasiz).

Ko'ndalang (cross-cutting) xizmat: barcha modul shu port orqali strukturali log yozadi,
metrika qayd etadi va bajarilish vaqtini (span) o'lchaydi. ``trace_id`` orqali butun
so'rov oqimi uchdan-uchgacha bog'lanadi.

Implementatsiya ``providers/observability/`` da. Kelajakda OpenTelemetry — port o'zgarmaydi.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Observability(Protocol):
    """Kuzatuvchanlik: strukturali log, metrika va span."""

    def log(self, level: str, message: str, /, **fields: Any) -> None:
        """Strukturali log yozadi.

        Args:
            level: ``"debug"``/``"info"``/``"warning"``/``"error"``.
            message: Inson o'qiydigan xabar.
            **fields: Qo'shimcha strukturali maydonlar (sir/PII YOZILMAYDI).
        """
        ...

    def metric(self, name: str, value: float = 1.0, /, **tags: str) -> None:
        """Metrika (hisoblagich/o'lchov) qayd etadi.

        Args:
            name: Metrika nomi (masalan ``"llm.tokens"``).
            value: Qo'shiladigan qiymat (default 1.0 — hisoblagich).
            **tags: Kesim uchun teglar (masalan ``provider="claude"``).
        """
        ...

    def span(self, name: str, *, trace_id: str | None = None) -> AbstractContextManager[str]:
        """Bajarilish oralig'ini (span) o'lchaydi — kontekst-menejer.

        ``with obs.span("agent.chat") as tid: ...`` ko'rinishida ishlatiladi; davomiylik
        avtomatik o'lchanadi. Yielded qiymat — ``trace_id`` (berilmasa yangi yaratiladi).
        """
        ...
