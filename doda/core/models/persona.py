"""``Persona`` — DODA'ning barqaror shaxsiyati va tizim-prompti (versiyalangan asset).

Prompt kodda tarqoq emas — bitta versiyalangan modelda. ``render()`` foydalanuvchi profili va
tegishli xotira bilan to'liq tizim-promptini quradi (Agent shuni LLM'ga beradi).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from doda.core.models.memory import MemoryItem

_DEFAULT_IDENTITY = (
    "Sening isming DODA — Muhammadxo'ja yaratgan shaxsiy sun'iy intellekt yordamchi. "
    "Sen bu Mac kompyuterni HAQIQATAN boshqara olasan, chunki senda asboblar bor: "
    "URL/ilova/faylni ochish ('open'), terminal buyrug'i ('run_shell'), fayllar bilan ishlash, "
    "clipboard, bildirishnoma, joriy vaqt. Foydalanuvchi biror amalni so'rasa (masalan "
    '"YouTube\'ni och", "kalkulyatorni och"), \'men buni qila olmayman\' DEB AYTMA — mos '
    "asbobni ISHLAT va bajar. Faqat rostdan imkonsiz bo'lsagina uzr so'ra. "
    "HAR DOIM o'zbek tilida, qisqa va tabiiy javob ber. Markdown yoki emoji ishlatma "
    "(javobing ovoz orqali ham o'qilishi mumkin)."
)


@dataclass(frozen=True, slots=True)
class Persona:
    """DODA shaxsiyati (versiyalangan tizim-prompt)."""

    name: str = "DODA"
    version: str = "1.1"
    identity: str = _DEFAULT_IDENTITY

    def render(
        self,
        memories: Sequence[MemoryItem] = (),
        profile: Sequence[MemoryItem] = (),
    ) -> str:
        """To'liq tizim-promptini quradi (identity + profil + tegishli xotira)."""
        parts = [self.identity]
        if profile:
            parts.append("Foydalanuvchi haqida: " + "; ".join(item.content for item in profile))
        if memories:
            parts.append("Tegishli xotira: " + "; ".join(item.content for item in memories))
        return "\n\n".join(parts)
