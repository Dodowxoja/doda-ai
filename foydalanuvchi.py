# -*- coding: utf-8 -*-
"""
Foydalanuvchi QO'SHGAN buyruqlar (ovoz/bot orqali jonli qo'shiladi).

Bazaviy buyruqlar data/buyruqlar.json va data/javoblar.json da (o'zgarmaydi).
Foydalanuvchi qo'shganlari ALOHIDA data/foydalanuvchi.json da saqlanadi va
yuklashda bazaviylar ustiga qo'shiladi. Shunda base pack toza qoladi.

Sxema (data/foydalanuvchi.json):
{
  "apps":       {"kalit": "Ilova nomi"},
  "sites":      {"kalit": "https://..."},
  "folders":    {"kalit": "~/yol"},
  "komandalar": [[["kalit1","kalit2"], "tur", "arg"]],
  "javoblar":   [[["kalit1"], ["javob1","javob2"], "til"]]
}
"""
import os
import json

_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(_DIR, "data", "foydalanuvchi.json")

_BOSH = {"apps": {}, "sites": {}, "folders": {}, "komandalar": [], "javoblar": []}


def load():
    """foydalanuvchi.json ni o'qiydi (yo'q bo'lsa bo'sh sxema qaytaradi)."""
    try:
        with open(USER_FILE, encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {k: (dict(v) if isinstance(v, dict) else list(v)) for k, v in _BOSH.items()}
    # Yetishmagan kalitlarni to'ldiramiz
    for k, v in _BOSH.items():
        data.setdefault(k, dict() if isinstance(v, dict) else list())
    return data


def _save(data):
    os.makedirs(os.path.dirname(USER_FILE), exist_ok=True)
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_app(key, app_name):
    d = load()
    d["apps"][key.strip().lower()] = app_name.strip()
    _save(d)


def add_site(key, url):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    d = load()
    d["sites"][key.strip().lower()] = url
    _save(d)


def add_folder(key, path):
    d = load()
    d["folders"][key.strip().lower()] = path.strip()
    _save(d)


def add_javob(keywords, responses, lang="uz"):
    d = load()
    d["javoblar"].append([keywords, responses, lang])
    _save(d)


def add_komanda(keywords, tur, arg=None):
    d = load()
    d["komandalar"].append([keywords, tur, arg])
    _save(d)


def remove(trigger):
    """Foydalanuvchi qo'shgan buyruqni kalit so'zi bo'yicha o'chiradi. Nechta o'chirilgani qaytadi."""
    t = trigger.strip().lower()
    d = load()
    n = 0
    for grp in ("apps", "sites", "folders"):
        if t in d[grp]:
            del d[grp][t]
            n += 1
    before = len(d["javoblar"]) + len(d["komandalar"])
    d["javoblar"] = [j for j in d["javoblar"] if t not in [k.lower() for k in j[0]]]
    d["komandalar"] = [c for c in d["komandalar"] if t not in [k.lower() for k in c[0]]]
    n += before - (len(d["javoblar"]) + len(d["komandalar"]))
    _save(d)
    return n


def summary():
    """Qo'shilgan buyruqlarni o'qiladigan ro'yxat qilib qaytaradi (matn)."""
    d = load()
    lines = []
    for key, app in d["apps"].items():
        lines.append("ilova: '%s' -> %s" % (key, app))
    for key, url in d["sites"].items():
        lines.append("sayt: '%s' -> %s" % (key, url))
    for key, path in d["folders"].items():
        lines.append("papka: '%s' -> %s" % (key, path))
    for kw, resp, lang in d["javoblar"]:
        lines.append("javob: '%s' -> %s" % (", ".join(kw), resp[0] if resp else ""))
    for kw, tur, arg in d["komandalar"]:
        lines.append("buyruq: '%s' -> %s/%s" % (", ".join(kw), tur, arg))
    return lines
