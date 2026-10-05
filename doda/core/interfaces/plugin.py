"""Plugin portlari — ``Plugin`` va ``PluginContext``.

Plugin — yadroga tegmasdan yangi imkoniyat qo'shuvchi mustaqil modul (asboblar, hodisa-
tinglovchilar). Plugin ``setup`` da ``PluginContext`` orqali o'zini ro'yxatga oladi. Yadro
plugin haqida hech narsa bilmaydi — bu 4 barqaror kengaytirish nuqtasidan biri.

XAVFSIZLIK (ADR-017 Autonomy Boundary): pluginlar faqat foydalanuvchi sozlagan holda
yuklanadi; DODA o'zini o'zi yashirin o'zgartirmaydi.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from code.doda.core.interfaces.bus import EventHandler
from code.doda.core.interfaces.tool import Tool


@runtime_checkable
class PluginContext(Protocol):
    """Plugin o'zini ro'yxatga oladigan cheklangan interfeys (yadroga bevosita kirmaydi)."""

    def register_tool(self, tool: Tool) -> None:
        """Yangi asbobni Agent uchun ro'yxatga qo'shadi."""
        ...

    def subscribe(self, event: str, handler: EventHandler) -> None:
        """Plugin handlerini hodisaga obuna qiladi (teardown'da bekor qilinadi)."""
        ...


@runtime_checkable
class Plugin(Protocol):
    """Mustaqil kengaytma moduli."""

    @property
    def name(self) -> str:
        """Plugin nomi (registrda noyob)."""
        ...

    @property
    def version(self) -> str:
        """Plugin versiyasi (semver)."""
        ...

    async def setup(self, context: PluginContext) -> None:
        """Pluginni ishga tayyorlaydi (asbob/hodisa ro'yxatga olinadi)."""
        ...

    async def teardown(self) -> None:
        """Plugin resurslarini tozalaydi (o'chirilganda)."""
        ...
