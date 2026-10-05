# -*- coding: utf-8 -*-
"""
BUYRUQLAR.md ni AVTOMATIK yaratadi (buyruq_baza.py + javoblar.py dan).

Qo'lда tahrirlamang — buyruq qo'shsangiz, shu skript yangilaydi.
Ishga tushirish:  python3 royxat_yarat.py
(asistent.py ham har ishga tushganда buni chaqiradi.)
"""
import os
import code.buyruq_baza as b

try:
    from code.javoblar import JAVOBLAR
except Exception:
    JAVOBLAR = []

# KOMANDALAR turlari uchun sarlavha va emoji
TUR_SARLAVHA = {
    "sms": "✉️ SMS / Xabar yuborish",
    "call": "📞 Qo'ng'iroq (FaceTime)",
    "play": "▶️ Qo'shiq/video o'ynatish (YouTube)",
    "media": "🎵 Media (musiqa/video)",
    "system": "⚙️ Tizim boshqaruvi",
    "time": "🕐 Vaqt va sana",
    "timer": "⏲️ Timer",
    "stopwatch": "⏱️ Sekundomer",
    "dev": "💻 Developer buyruqlari",
    "weather": "🌤️ Ob-havo (bugun/ertaga)",
    "news": "📰 Yangiliklar",
    "prayer": "🕌 Namoz vaqtlari",
    "wiki": "📚 Wikipedia (ma'lumot)",
    "quit": "❌ Ilovani yopish",
    "email": "📧 Email",
    "calendar": "📆 Kalendar",
    "convert": "🔢 Konvertor (valyuta/o'lchov)",
    "currency": "💵 Valyuta kursi",
    "crypto": "🪙 Kripto narxlari",
    "translate": "🌍 Tarjima",
    "math": "🧮 Hisoblash",
    "note": "📝 Qayd (Notes)",
    "voice": "🎙️ Ovoz jinsi (erkak/ayol)",
    "emotion": "🎭 Hissiyot ohangi (hursand/hafa/jahl/xotirjam)",
    "screen": "🖥️ Ekranni boshqarish (nusxa/joylashtir/scroll/oyna)",
    "type": "⌨️ Klaviaturadan matn yozdirish",
    "vision": "👁️ Ko'rish (kamera/ekran — narsa/amal, yuz xotira)",
    "reply": "💬 Boshqa",
}


def _uniq(values):
    seen, out = set(), []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def yarat(path=None):
    """BUYRUQLAR.md ni yaratadi/yangilaydi."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "BUYRUQLAR.md")

    L = []
    L.append("# 🎙 DODA — Buyruqlar ro'yxati")
    L.append("")
    L.append("> Bu fayl **avtomatik** yaratiladi (`royxat_yarat.py`). Qo'lда tahrirlamang —")
    L.append("> yangi buyruq qo'shsangiz `buyruq_baza.py` yoki `javoblar.py` ga qo'shing, ro'yxat o'zi yangilanadi.")
    L.append("")
    L.append("Buyruqlarni **ovoz bilan ayting** yoki **matn qilib yozing** (o'zbek yoki rus tilida).")
    L.append("")

    # --- Ilovalar ---
    L.append("## 🖥 Ilovalarni ochish")
    L.append("Ayting: `<ilova> och` (masalan `chrome och`, `telegram och`)")
    L.append("")
    for app in _uniq(b.APPS.values()):
        L.append("- " + app)
    L.append("")

    # --- Saytlar ---
    L.append("## 🌐 Saytlarni ochish")
    L.append("Ayting: `<sayt> och` (masalan `youtube och`)")
    L.append("")
    for name in _uniq(b.SITES.keys()):
        if name.isascii():  # ruscha dublikatlarni tashlaymiz
            L.append("- " + name)
    L.append("")

    # --- Papkalar ---
    L.append("## 📁 Papkalarni ochish")
    L.append("Ayting: `<papka> och` (masalan `downloads och`)")
    L.append("")
    for name in _uniq(b.FOLDERS.keys()):
        if name.isascii():
            L.append("- " + name)
    L.append("")

    # --- Qidiruv ---
    L.append("## 🔎 Qidiruv")
    L.append("Ayting: `googleda <so'rov> qidir`, `youtubeда <so'rov> qidir`")
    L.append("")

    # --- KOMANDALAR turlar bo'yicha ---
    turlar = {}
    for keywords, typ, arg in b.KOMANDALAR:
        turlar.setdefault(typ, []).append(keywords[0])
    for typ, sarlavha in TUR_SARLAVHA.items():
        if typ not in turlar:
            continue
        L.append("## " + sarlavha)
        for kw in turlar[typ]:
            L.append("- `" + kw + "`")
        L.append("")

    # --- Maxsus (kodда special-case) ---
    L.append("## ⏰ Eslatma")
    L.append("- `soat 10:00 da uchrashuvim bor eslat` — o'sha vaqtda eslatadi")
    L.append("")
    L.append("## 🔐 Bot paroli")
    L.append("- `parol ber` — Telegram botga kirish uchun 6 xonali bir martalik parol")
    L.append("")
    L.append("## 👋 Xayrlashuv (chiqish)")
    L.append("- `xayr` (o'zbekcha javob) / `пока` (ruscha javob) — dastur to'xtaydi")
    L.append("")

    # --- Suhbat javoblari (javoblar.py) ---
    L.append("## 💬 Suhbat")
    L.append("Salomlashish, minnatdorchilik, hazil va boshqalar. Namunaviy iboralar:")
    L.append("")
    for entry in JAVOBLAR:
        kw = entry[0][0] if entry and entry[0] else ""
        if kw:
            L.append("- `" + kw + "`")
    L.append("")

    # --- Statistika ---
    L.append("---")
    L.append("_Ilovalar: %d · Saytlar: %d · Papkalar: %d · Harakat buyruqlari: %d · Suhbat: %d_"
             % (len(_uniq(b.APPS.values())), len(_uniq(b.SITES.keys())),
                len(_uniq(b.FOLDERS.keys())), len(b.KOMANDALAR), len(JAVOBLAR)))

    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")
    return path


if __name__ == "__main__":
    p = yarat()
    print("Yaratildi:", p)
