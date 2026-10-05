# -*- coding: utf-8 -*-
"""
DODA buyruqlar bazasi — YUKLOVCHI.

Buyruqlar endi JSON da saqlanadi (koddan to'liq ajratilgan):
  data/buyruqlar.json    -> bazaviy (pack) buyruqlar: APPS, SITES, FOLDERS, SEARCH_ENGINES, KOMANDALAR
  data/foydalanuvchi.json-> foydalanuvchi ovoz/bot orqali QO'SHGAN buyruqlar (bazaviy ustiga qo'shiladi)

Bu fayl faqat o'sha JSON'larni o'qib, quyidagilarni tayyorlaydi:
  APPS, SITES, FOLDERS  -> {kalit: qiymat} lug'atlar
  SEARCH_ENGINES        -> {nom: qidiruv-URL}
  KOMANDALAR            -> [ [ [kalitlar...], tur, arg ] ... ]  (tur handleri asistent.py da)

Yangi buyruq qo'shish: JSON faylni tahrirlang YOKI DODA'ga "ilova qo'sh / sayt qo'sh / javob qo'sh" deng.
"""
import os
import json

import foydalanuvchi as foydalanuvchi

_DIR = os.path.dirname(os.path.abspath(__file__))
_BUYRUQLAR_JSON = os.path.join(_DIR, "data", "buyruqlar.json")


def _load_base():
    try:
        with open(_BUYRUQLAR_JSON, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print("data/buyruqlar.json yuklanmadi:", e)
        return {"APPS": {}, "SITES": {}, "FOLDERS": {}, "SEARCH_ENGINES": {}, "KOMANDALAR": []}


def reload():
    """Bazaviy + foydalanuvchi JSON'larini qayta o'qib, global datani yangilaydi.
    Lug'at/ro'yxatlar JOYIDA yangilanadi — asistent.py import qilgan obyektlar ham yangilanadi."""
    base = _load_base()
    user = foydalanuvchi.load()

    # Lug'atlarni joyida (in-place) yangilaymiz: base, keyin foydalanuvchi ustiga
    for name, extra in (("APPS", "apps"), ("SITES", "sites"), ("FOLDERS", "folders")):
        d = globals()[name]
        d.clear()
        d.update(base.get(name, {}))
        d.update(user.get(extra, {}))

    SEARCH_ENGINES.clear()
    SEARCH_ENGINES.update(base.get("SEARCH_ENGINES", {}))

    # KOMANDALAR: foydalanuvchiniki BIRINCHI (ustunlik), keyin bazaviy
    KOMANDALAR[:] = list(user.get("komandalar", [])) + list(base.get("KOMANDALAR", []))


# Global konteynerlar (asistent.py shularni import qiladi — obyekt o'zgarmaydi, ichi yangilanadi)
APPS = {}
SITES = {}
FOLDERS = {}
SEARCH_ENGINES = {}
KOMANDALAR = []

reload()
