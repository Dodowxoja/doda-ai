"""PLUGINS qatlami — yadroga tegmasdan imkoniyat qo'shuvchi mustaqil modullar.

``PluginManager`` pluginlarni yuklaydi; ``DefaultPluginContext`` ularni asbob-registri va
hodisa-avtobusiga ulaydi. Yangi imkoniyat = yangi plugin (4 barqaror kengaytirish nuqtasidan biri).
"""

from doda.plugins.context import DefaultPluginContext
from doda.plugins.manager import PluginManager

__all__ = ["DefaultPluginContext", "PluginManager"]
