"""LLM javobidan JSON ajratish yordamchilari (reja/hukm uchun).

LLM ba'zan JSON atrofida qo'shimcha matn qaytaradi; bu yerda birinchi ``[``…``]`` yoki
``{``…``}`` bloki ajratib olinadi va xavfsiz parse qilinadi (xato → ``None``).
"""

from __future__ import annotations

import json
from typing import Any


def extract_json_array(text: str) -> list[Any] | None:
    """Matndan birinchi JSON massivini ajratib parse qiladi; topilmasa/xato bo'lsa ``None``.

    ``[``…``]`` qavs-slicesi natija massiv (list) ekanini kafolatlaydi, shuning uchun
    qo'shimcha tur-tekshiruvi shart emas.
    """
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end <= start:
        return None
    try:
        result: list[Any] = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return result


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Matndan birinchi JSON obyektini ajratib parse qiladi; topilmasa/xato bo'lsa ``None``.

    ``{``…``}`` qavs-slicesi natija obyekt (dict) ekanini kafolatlaydi.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        result: dict[str, Any] = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return result
