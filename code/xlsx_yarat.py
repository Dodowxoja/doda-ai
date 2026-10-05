# -*- coding: utf-8 -*-
"""
Buyruqlarni xlsx faylga yozadi — o'zbekcha va ruscha ALOHIDA varaqlarda.
Ma'lumot: buyruq_baza.py + javoblar.py.

Ishga tushirish:  python3 xlsx_yarat.py
"""
import openpyxl
import code.buyruq_baza as b

try:
    from code.javoblar import JAVOBLAR
except Exception:
    JAVOBLAR = []

TUR = {
    "sms": "SMS", "call": "Qo'ng'iroq", "media": "Media", "system": "Tizim",
    "time": "Vaqt/Sana", "timer": "Timer", "stopwatch": "Sekundomer",
    "dev": "Developer", "weather": "Ob-havo", "wiki": "Wikipedia", "reply": "Ma'lumot",
}


def is_ru(s):
    return any("Ѐ" <= c <= "ӿ" for c in s)


def collect():
    uz, ru = [], []
    for k, app in b.APPS.items():
        if is_ru(k):
            ru.append(("Ilova", "открой " + k, app))
        else:
            uz.append(("Ilova", k + " och", app))
    for k, url in b.SITES.items():
        if is_ru(k):
            ru.append(("Sayt", "открой " + k, url))
        else:
            uz.append(("Sayt", k + " och", url))
    for k, p in b.FOLDERS.items():
        if is_ru(k):
            ru.append(("Papka", "открой " + k, p))
        else:
            uz.append(("Papka", k + " och", p))
    for kws, typ, arg in b.KOMANDALAR:
        cat = TUR.get(typ, typ)
        for kw in kws:
            (ru if is_ru(kw) else uz).append((cat, kw, ""))
    for entry in JAVOBLAR:
        kws, resp, lang = entry[0], entry[1], entry[2]
        if lang == "en":
            continue  # ingliz kerak emas
        tgt = ru if lang == "ru" else uz
        for kw in kws:
            tgt.append(("Suhbat", kw, resp[0] if resp else ""))
    return uz, ru


def yarat(path=None):
    import os
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DODA_buyruqlar_uz_ru.xlsx")
    uz, ru = collect()
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "O'zbekcha"
    ws1.append(["Kategoriya", "Buyruq", "Tavsif / Javob"])
    for row in uz:
        ws1.append(list(row))
    ws2 = wb.create_sheet("Ruscha")
    ws2.append(["Категория", "Команда", "Описание / Ответ"])
    for row in ru:
        ws2.append(list(row))
    # ustun kengligi
    for ws in (ws1, ws2):
        ws.column_dimensions["A"].width = 16
        ws.column_dimensions["B"].width = 32
        ws.column_dimensions["C"].width = 48
    wb.save(path)
    return path, len(uz), len(ru)


if __name__ == "__main__":
    p, nu, nr = yarat()
    print("Yaratildi:", p)
    print("O'zbekcha qatorlar:", nu, "| Ruscha qatorlar:", nr)
