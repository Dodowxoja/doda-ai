# -*- coding: utf-8 -*-
"""
DODA suhbat javoblari — YUKLOVCHI.

Javoblar endi JSON da:
  data/javoblar.json      -> bazaviy javoblar: [ [ [kalitlar...], [javoblar...], "til" ] ... ]
  data/foydalanuvchi.json -> foydalanuvchi QO'SHGAN javoblar (bazaviy oldiga qo'yiladi, ustunroq)

Yangi javob qo'shish: JSON'ni tahrirlang YOKI DODA'ga "javob qo'sh <so'z> = <javob>" deng.
"""
import os
import json

import code.foydalanuvchi as foydalanuvchi

_DIR = os.path.dirname(os.path.abspath(__file__))
_JAVOBLAR_JSON = os.path.join(_DIR, "data", "javoblar.json")


def _load_base():
    try:
        with open(_JAVOBLAR_JSON, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("data/javoblar.json yuklanmadi:", e)
        return []


def load_javoblar():
    """Foydalanuvchi javoblari BIRINCHI (ustunlik), keyin bazaviylar."""
    user = foydalanuvchi.load().get("javoblar", [])
    return list(user) + _load_base()


JAVOBLAR = load_javoblar()
