"""``Tool`` porti — DODA bajara oladigan bitta asbob (harakat qilish qobiliyati).

Asbob = LLM chaqira oladigan funksiya (JSON-schema parametrlar bilan). Konkret asboblar
``doda/tools/`` da; ``ToolRegistry`` ularni ``ToolExecutor`` sifatida jamlaydi (M4 tsikliga
ulanadi). Yangi asbob qo'shish = shu portning yangi implementatsiyasi (core o'zgarmaydi).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Nomlangan, chaqiriladigan asbob (LLM funksiya-chaqiruvi uchun)."""

    @property
    def name(self) -> str:
        """Asbob nomi (LLM shu nom bilan chaqiradi; registrda noyob)."""
        ...

    @property
    def description(self) -> str:
        """Asbob nima qilishi (LLM qachon chaqirishni shundan tushunadi)."""
        ...

    @property
    def parameters(self) -> Mapping[str, Any]:
        """Argumentlar JSON-schema ko'rinishida (LLM validatsiyasi uchun)."""
        ...

    async def run(self, arguments: Mapping[str, Any]) -> str:
        """Asbobni ``arguments`` bilan bajaradi va natija matnini qaytaradi."""
        ...
