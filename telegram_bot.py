# -*- coding: utf-8 -*-
"""
DODA Telegram bot — matn va ovozли xabar orqali boshqarish.

Xavfsizlik (OTP): botga kirish uchun bir martalik parol kerak.
  1) Kompyuterda DODA'ga "parol ber" deng -> u 6 xonali kod aytadi (~/.doda_otp fayliga yoziladi)
  2) Shu kodni botga yuboring -> bot ochiladi (kod bir martalik, ishlatilgach bekor bo'ladi)

Token (chatga tashlamang!):
  echo "YANGI_TOKEN" > ~/.doda_bot_token && chmod 600 ~/.doda_bot_token
  yoki:  export TELEGRAM_BOT_TOKEN="..."

Ishga tushirish:  python3 telegram_bot.py
"""
import os
import re
import json
import time
import fcntl
import asyncio
import logging
import secrets
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error
import datetime as dt

import speech_recognition as sr
from telegram import (Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
                      MenuButtonWebApp, WebAppInfo)
from telegram.error import NetworkError, TimedOut
from telegram.ext import (Application, CommandHandler, MessageHandler, filters,
                          ContextTypes, CallbackQueryHandler)

import code.asistent as asistent  # DODA motori (buyruqlarni bajaradi)
import code.foydalanuvchi as foydalanuvchi
import code.vision as vision      # ekran/kamera rasmini olish
import code.tarmoq as tarmoq      # uy tarmog'i monitoringi
import code.mac_system as mac_system  # batareya / CPU / RAM holati
import code.ruxsatlar as ruxsatlar   # macOS ruxsatlarini tekshirish (Screen/Accessibility/Full Disk/Camera)

_DIR = os.path.dirname(os.path.abspath(__file__))
OTP_FILE = os.path.expanduser("~/.doda_otp")
USERS_FILE = os.path.expanduser("~/.doda_bot_users")
ERROR_LOG = os.path.join(_DIR, "logs/bot_error.log")
OUT_LOG = os.path.join(_DIR, "logs/bot.log")
ERRORS_LOG = os.path.expanduser("logs/.doda_errors.log")   # markaziy xatolar (asistent + bot), /log shuni ko'rsatadi
HEARTBEAT_FILE = os.path.expanduser("~/.doda_bot_heartbeat")  # watchdog shuni kuzatadi
_lock = threading.Lock()

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)


# ---------- Token ----------
def load_token():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if tok:
        return tok.strip()
    p = os.path.expanduser("~/.doda_bot_token")
    if os.path.exists(p):
        return open(p).read().strip()
    return None


def validate_token(token):
    """Token yaroqli-yo'qligini getMe bilan tekshiradi.
    Faqat aniq 401/404 (token noto'g'ri) da False qaytaradi — tarmoq yo'q bo'lsa BLOKLAMAYDI."""
    try:
        with urllib.request.urlopen(
                "https://api.telegram.org/bot%s/getMe" % token, timeout=10) as r:
            return bool(json.load(r).get("ok"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 404):
            return False        # token yaroqsiz / bekor qilingan
        return True             # boshqa server xatosi -> tokenni ayblamaymiz
    except Exception:
        return True             # tarmoq yo'q -> poller o'zi qayta urinadi


# ---------- Avtorizatsiya (kim kirgan) ----------
def load_users():
    if os.path.exists(USERS_FILE):
        return set(int(x) for x in open(USERS_FILE).read().split() if x.strip().isdigit())
    return set()


def save_users(users):
    with open(USERS_FILE, "w") as f:
        f.write("\n".join(str(u) for u in users))
    os.chmod(USERS_FILE, 0o600)


# ---------- Egasi (OWNER): faqat BITTA Telegram ID to'liq boshqaradi ----------
# XAVFSIZLIK: ega FAQAT terminal orqali ~/.doda_owner_id fayliga QO'LDA yoziladi.
# OTP orqali "birinchi kirgan odam ega bo'lib qolishi" MUMKIN EMAS.
OWNER_FILE = os.path.expanduser("~/.doda_owner_id")


def load_owner():
    """Saqlangan egasining chat_id'sini qaytaradi yoki None (hali belgilanmagan)."""
    try:
        s = open(OWNER_FILE).read().strip()
        return int(s) if s.isdigit() else None
    except Exception:
        return None


OWNER_ID = load_owner()
# Avtorizatsiya YAGONA manba — egasi fayli. ~/.doda_bot_users faqat egadan iborat
# (watchdog/uygotkich/dashboard shundan kimga xabar berishni biladi).
if OWNER_ID is not None:
    AUTHORIZED = {OWNER_ID}
    try:
        save_users(AUTHORIZED)
    except Exception:
        pass
else:
    AUTHORIZED = set()


def is_owner(chat_id):
    """Faqat egasiga True. Egasi hali belgilanmagan bo'lsa hech kimga True emas."""
    return OWNER_ID is not None and int(chat_id) == OWNER_ID


def authorize_if_owner(chat_id):
    """Faylдаги egaga qarab avtorizatsiya (faylни har safar yangi o'qiydi).
    Qaytaradi: True=ega (kirdi), 'no_owner'=ega belgilanmagan, False=begona."""
    global OWNER_ID, AUTHORIZED
    OWNER_ID = load_owner()                 # qo'lда o'zgartirish darrov ta'sir qilsin
    if OWNER_ID is None:
        return "no_owner"
    if int(chat_id) == OWNER_ID:
        AUTHORIZED = {OWNER_ID}
        try:
            save_users(AUTHORIZED)
        except Exception:
            pass
        return True
    return False


async def _alert_owner_intrusion(context, intruder_id, update):
    """Begona ID to'g'ri OTP bilan kirishga urinsa — egasini ogohlantiradi."""
    uname = ""
    try:
        u = update.effective_user
        uname = (" @" + u.username) if getattr(u, "username", None) else ""
    except Exception:
        pass
    msg = ("🚨 Ogohlantirish: begona hisob (ID %s%s) to'g'ri parol bilan "
           "kirishga urindi, lekin rad etildi. Agar bu siz bo'lmasangiz, "
           "kompyuterda «yangi parol» bermang." % (intruder_id, uname))
    if OWNER_ID:
        try:
            await context.bot.send_message(chat_id=OWNER_ID, text=msg)
        except Exception:
            pass


def check_otp(entered):
    """Fayldagi bir martalik parolni tekshiradi. To'g'ri bo'lsa bekor qiladi."""
    if not os.path.exists(OTP_FILE):
        return False
    code = open(OTP_FILE).read().strip()
    if code and entered.strip() == code:
        os.remove(OTP_FILE)  # bir martalik -> bekor
        return True
    return False


# ---------- Ovozni matnga ----------
def transcribe_wav(wav_path):
    r = sr.Recognizer()
    with sr.AudioFile(wav_path) as src:
        audio = r.record(src)
    try:
        text = asistent._recognize_online(audio)
        if text:
            return text
    except Exception:
        pass
    return asistent._recognize_offline(audio)


# ---------- Eslatma (Telegram orqali, faylga saqlanadi) ----------
REMINDERS_FILE = os.path.expanduser("~/.doda_reminders.json")


def _human_delay(delay):
    if delay >= 3600:
        return str(delay // 3600) + " soatdan keyin"
    if delay >= 60:
        return str(delay // 60) + " daqiqadan keyin"
    return str(delay) + " soniyadan keyin"


def _load_pending():
    try:
        if os.path.exists(REMINDERS_FILE):
            return json.load(open(REMINDERS_FILE))
    except Exception:
        pass
    return []


def _save_pending(items):
    try:
        with open(REMINDERS_FILE, "w") as f:
            json.dump(items, f)
    except Exception:
        pass


def _add_pending(chat_id, fire_ts, note):
    items = _load_pending()
    items.append({"chat_id": chat_id, "fire": fire_ts, "note": note})
    _save_pending(items)


def _remove_pending(chat_id, fire_ts, note):
    items = [x for x in _load_pending()
             if not (x.get("chat_id") == chat_id and x.get("fire") == fire_ts and x.get("note") == note)]
    _save_pending(items)


async def _send_reminder(bot, chat_id, delay, note, fire_ts):
    await asyncio.sleep(max(delay, 0))
    try:
        await bot.send_message(chat_id=chat_id, text="⏰ Eslatma: " + note)
    except Exception:
        pass
    finally:
        _remove_pending(chat_id, fire_ts, note)


async def _recurring_loop(app):
    """Takroriy eslatmalarni (har kuni/ish kunlari) fonда kuzatadi + heartbeat yozadi."""
    while True:
        # Watchdog uchun "tirikman" belgisi
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                f.write(str(int(time.time())))
        except Exception:
            pass
        now = dt.datetime.now()
        for it in asistent.pop_due_recurring(now, lambda c: c != "local"):
            try:
                await app.bot.send_message(chat_id=it["chat_id"], text="⏰ Eslatma: " + it["note"])
            except Exception:
                pass
        # Quvvatда: har 20s; batareyaда: har 45s (watchdog 150s chegarasidan xavfsiz ичida)
        await asyncio.sleep(45 if _on_battery() else 20)


def _on_battery():
    """Hozir batareyaда (quvvatga ulanmaganmi)? True/False. Xato bo'lsa False (ehtiyot)."""
    try:
        out = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=4).stdout
        return "discharging" in out.lower()
    except Exception:
        return False


async def _network_loop(app):
    """Uy tarmog'ini fonда kuzatadi — yangi qurilma paydo bo'lsa ogohlantiradi.
    Resurs tejash: batareyaда siyrakroq skanerlaydi."""
    first = True
    while True:
        try:
            yangi = await asyncio.to_thread(tarmoq.update)
            if yangi and not first:      # birinchi skanerda ogohlantirmaymiz (bazani to'ldiramiz)
                lines = "\n".join("• %s (%s)" % (d["ip"], d["mac"]) for d in yangi)
                msg = "🆕 Tarmoqqa yangi qurilma ulandi (%d ta):\n%s" % (len(yangi), lines)
                for uid in list(AUTHORIZED):
                    try:
                        await app.bot.send_message(chat_id=uid, text=msg)
                    except Exception:
                        pass
        except Exception as e:
            logging.warning("network loop xato: %s", e)
        first = False
        # Quvvatда: har 5 daqiqa; batareyaда: har 15 daqiqa (quvvat tejash)
        await asyncio.sleep(900 if _on_battery() else 300)


_bg_tasks = []   # fon tsikllari (o'chishda toza bekor qilinadi)


async def _post_init(app):
    """Bot ishga tushganda: / menyusini o'rnatadi + eslatmalarni tiklaydi."""
    try:
        await app.bot.set_my_commands([
            BotCommand("start", "Botni boshlash / kirish"),
            BotCommand("panel", "Tugmali boshqaruv paneli"),
            BotCommand("ekran", "🖥 Ekran rasmini yuborish"),
            BotCommand("kamera", "📷 Kamera rasmini yuborish"),
            BotCommand("holat", "💻 Batareya / CPU / xotira"),
            BotCommand("tarmoq", "📡 Uy tarmog'idagi qurilmalar"),
            BotCommand("ruxsat", "🔐 macOS ruxsatlarini tekshirish"),
            BotCommand("app", "🎙 DODA Mini App (to'liq panel)"),
            BotCommand("buyruqlar", "📋 Barcha buyruqlar ro'yxati"),
            BotCommand("log", "🛠 Xatolar jurnali"),
        ])
    except Exception as e:
        logging.warning("set_my_commands ishlamadi: %s", e)
    # Chat yonidagi "Menu" tugmasini Mini App qilamiz (tunnel tayyor bo'lsa)
    try:
        url = _tunnel_url_tok()
        if url:
            await app.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="DODA", web_app=WebAppInfo(url=url)))
    except Exception as e:
        logging.warning("menu button ishlamadi: %s", e)
    _bg_tasks.append(asyncio.create_task(_network_loop(app)))
    await _restore_reminders(app)


async def _shutdown(app):
    """Bot o'chganda fon tsikllarini TOZA to'xtatadi (asyncio ogohlantirishlarisiz)."""
    for t in _bg_tasks:
        t.cancel()
    if _bg_tasks:
        await asyncio.gather(*_bg_tasks, return_exceptions=True)
    _bg_tasks.clear()


async def _restore_reminders(app):
    """Bot qayta yuklanганда saqlangan eslatmalarni tiklaydi + takroriy loopни boshlaydi."""
    _bg_tasks.append(asyncio.create_task(_recurring_loop(app)))
    now = time.time()
    for item in list(_load_pending()):
        remaining = item.get("fire", 0) - now
        if remaining > 0:
            asyncio.create_task(_send_reminder(app.bot, item["chat_id"], remaining, item["note"], item["fire"]))
        else:
            try:
                await app.bot.send_message(chat_id=item["chat_id"], text="⏰ (kechikkan) Eslatma: " + item["note"])
            except Exception:
                pass
            _remove_pending(item["chat_id"], item["fire"], item["note"])


# ---------- Buyruqlar menyusi ----------
def build_menu():
    """/buyruqlar uchun toifalarga bo'lingan buyruqlar ro'yxati + foydalanuvchi qo'shganlari."""
    m = [
        "📋 *DODA buyruqlari*",
        "",
        "🖥 *Ilova / sayt / papka ochish*",
        "  «chrome och», «telegram och», «youtube och», «downloads och»",
        "",
        "🔊 *Tizim*",
        "  «ovozni oshir/pasaytir», «ovozsiz qil», «yorug'likni oshir»,",
        "  «wifi yoq/o'chir», «skrinshot», «uxla»",
        "  «sistemani tekshir» — batareya + CPU + RAM birga",
        "  «batareya» · «buferda nima bor» (clipboard matni)",
        "",
        "🕐 *Vaqt / sana*",
        "  «soat nechi», «bugun sana», «qaysi kun», «namoz vaqtlari»",
        "",
        "⏰ *Eslatma*",
        "  «2 soatdan keyin suv ich eslat», «soat 10 da majlis eslat»,",
        "  «har kuni soat 8 da eslat», «eslatmalarim»",
        "",
        "🌤 *Ma'lumot*",
        "  «ob havo», «ertaga ob havo», «yangiliklar», «valyuta kursi»,",
        "  «1 dollar necha som», «bitcoin narxi», «wikipedia Eynshteyn»",
        "",
        "🌐 *Tarjima / hisob*",
        "  «salom ni inglizchaga tarjima qil», «25 karra 4», «100 dollar necha som»",
        "",
        "🎵 *Media / ovoz*",
        "  «musiqa qo'y», «pauza», «keyingi», «Ummon qo'shig'ini qo'y»,",
        "  «ayol ovozida gapir», «hursand gapir»",
        "",
        "📞 *Aloqa*",
        "  «email yoz … ga …», «sms yoz … ga …», «qo'ng'iroq qil …»",
        "",
        "🖥 *Masofadan boshqarish (uzoqdan)*",
        "  «ekranni ko'rsat» / «screen tasha» — ekranni tiniq yuboradi",
        "  «kamerani ko'rsat» — kamera rasmini yuboradi",
        "  «video tasha» — 5 soniyalik ekran videosi",
        "  «kamera video» — 5 soniyalik kamera videosi",
        "  «nima ochiq» — qaysi ilova/oyna ochiqligini aytadi",
        "  «papka yarat <nom>» / «fayl yarat <nom>» — ish stolida yaratadi",
        "  «papkalarni yop» — barcha Finder oynalarini yopadi",
        "  «oynani yop» — old oynani yopadi",
        "  «buyruq bajar ls ~/Desktop» — terminal buyrug'i (tasdiqlash bilan)",
        "  «avto skrin yoq» — biror narsa ochilsa/o'zgarsa ekranni o'zi yuboradi",
        "  «avto skrinni o'chir» — buni to'xtatadi",
        "",
        "🏠 *Uy tarmog'i*",
        "  «kim ulandi» / «qurilmalar» — Wi-Fi'ga ulanganlar ro'yxati",
        "  «wifi'ni uy deb saqla» — hozirgi Wi-Fi'ni uy qilib belgilaydi",
        "  (yangi qurilma paydo bo'lsa bot o'zi ogohlantiradi; router 🛜 belgili)",
        "",
        "➕ *O'z buyrug'ingni qo'shish*",
        "  «sayt qo'sh olx = olx.uz»",
        "  «ilova qo'sh telefon = Phone»",
        "  «javob qo'sh <so'z> = <javob>»",
        "  «qo'shilgan buyruqlar»  ·  «buyruqni o'chir <so'z>»",
        "",
        "🛠 /log — xatolar jurnali",
    ]
    custom = foydalanuvchi.summary()
    if custom:
        m.append("")
        m.append("⭐️ *Siz qo'shgan buyruqlar:*")
        for c in custom[:30]:
            m.append("  • " + c)
    return "\n".join(m)


# ---------- Log yordamchilari ----------
def read_log_tail(path, n=30):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-n:]).strip()
    except FileNotFoundError:
        return ""


def clean_logs():
    """Log fayllarni bo'shatadi (xatolar tarixini o'chiradi)."""
    for p in (ERRORS_LOG, ERROR_LOG, OUT_LOG):
        try:
            open(p, "w").close()
        except Exception:
            pass


def prune_errors(max_age_min=30):
    """Eski (ehtimol tuzalgan) xatolarni jurnaldan olib tashlaydi.
    Mantiq: xato max_age_min daqiqadan beri qaytarilmagan bo'lsa -> tuzalgan deb hisoblaymiz.
    (qolgan, o'chirilgan) sonini qaytaradi."""
    try:
        with open(ERRORS_LOG, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except FileNotFoundError:
        return 0, 0
    if not content.strip():
        return 0, 0
    # Har bir yozuv timestamp bilan boshlanadi -> shu bo'yicha bloklarga ajratamiz
    parts = re.split(r"(?m)(?=^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} )", content)
    cutoff = dt.datetime.now() - dt.timedelta(minutes=max_age_min)
    kept, removed = [], 0
    for blk in parts:
        if not blk.strip():
            continue
        m = re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", blk)
        if m:
            try:
                ts = dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if ts < cutoff:
                    removed += 1
                    continue
            except ValueError:
                pass
        kept.append(blk)
    try:
        with open(ERRORS_LOG, "w", encoding="utf-8") as f:
            f.write("".join(kept))
    except Exception:
        pass
    return len(kept), removed


# ---------- Masofaviy boshqaruv: ekran/kamera rasmi + terminal ----------
def wants_video(text):
    """'screen' | 'camera' | None — 5 soniyalik video so'raganmi ('video' so'zi bilan)."""
    low = asistent._norm(text)
    if "video" not in low and "видео" not in low:
        return None
    if any(k in low for k in ("kamera", "selfi", "webcam", "veb kamera", "o'zim", "ozim", "yuz")):
        return "camera"
    # video + (ekran/screen) yoki shunchaki "video tashla" -> ekran
    return "screen"


def wants_image(text):
    """'screen' | 'camera' | None — foydalanuvchi ekran/kamera rasmini so'raganmi."""
    low = asistent._norm(text)
    if any(k in low for k in ("ekranni korsat", "ekranni yubor", "ekran rasmi", "ekran surat",
                              "ekranni ol", "skrinshot", "screenshot", "kompyuterni korsat",
                              "kompni korsat", "ekran tashla", "ekranni tashla",
                              "skrin tashla", "skrin tasha", "skrin yubor", "skrin ol", "skrinni yubor",
                              "screen tashla", "screen tasha", "screen yubor", "skreen tashla",
                              "skreen tasha", "skreen yubor", "ekran tasha", "ekranni tasha",
                              "ekranni ber", "skrin ber", "покажи экран", "скрин")):
        return "screen"
    if any(k in low for k in ("kamerani korsat", "kamera rasmi", "kamerani yubor",  # (kameravideo pastda ushlanadi)
                              "kamerani ol",
                              "rasmga ol", "selfi", "webcam", "veb kamera", "kamera tashla",
                              "kamera tasha", "kamerani tashla", "kamerani tasha", "kamera ber",
                              "kamera yubor", "kamerani yubor",
                              # «meni ko'ryapsanmi / rasmimni tashla» — ko'rayotganini ISBOTLASH uchun
                              "meni koryapsanmi", "meni korayapsanmi", "meni korabsanmi",
                              "meni koryabsanmi", "koryapsanmi", "korayapsanmi", "korasanmi",
                              "meni korsat", "meni korsatchi", "meni ko'rsat", "yuzimni korsat",
                              "rasmimni tashla", "rasmimni tasha", "rasmimni yubor", "rasmimni ol",
                              "meni rasmga ol", "meni ol", "meni tasha", "menga qara",
                              "видишь меня", "покажи меня", "мое фото")):
        return "camera"
    return None


_SHELL_PREFIX = ("buyruq bajar ", "komanda bajar ", "terminalda bajar ",
                 "terminal buyrugi ", "terminal buyrug'i ", "shell ", "bash ")
_DANGER = ("rm ", "rm-", "sudo", "shutdown", "reboot", "mkfs", " dd ", "diskutil",
           "killall", "chmod -r", "chown -r", ":(){", "> /dev", "format", "eraseall")


def extract_shell(text):
    """Terminal buyrug'ini ajratadi (aniq marker bilan; 'terminal och' bunga tushmaydi)."""
    t = text.strip()
    low = t.lower()
    for pfx in _SHELL_PREFIX:
        if low.startswith(pfx):
            return t[len(pfx):].strip()
    if t.startswith("$ "):
        return t[2:].strip()
    return None


def is_dangerous(cmd):
    low = " " + cmd.lower() + " "
    return any(d in low for d in _DANGER)


def run_shell(cmd, timeout=30):
    """Shell buyrug'ini bajaradi, (natija_matni, chiqish_kodi) qaytaradi."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = ((r.stdout or "") + (r.stderr or "")).strip()
        return (out or "(natija bo'sh)"), r.returncode
    except subprocess.TimeoutExpired:
        return "(vaqt tugadi: %ss)" % timeout, -1
    except Exception as e:
        return "xato: " + str(e), -1


_pending_cmds = {}   # qisqa_id -> (chat_id, buyruq)
_pending_tg = {}     # qisqa_id -> (chat_id, recipient, text) — tasdiqlanmagan Telegram xabari


AUTOSHOT_FILE = os.path.expanduser("~/.doda_autoshot")   # avto-skrin yoqiqmi (bo'lsa = yoqiq)


def autoshot_on():
    return os.path.exists(AUTOSHOT_FILE)


def set_autoshot(on):
    if on:
        open(AUTOSHOT_FILE, "w").close()
    elif os.path.exists(AUTOSHOT_FILE):
        os.remove(AUTOSHOT_FILE)


# Vizual o'zgarish qiladigan buyruqlar (bajarilgach avto-skrin yuboriladi).
# Ma'lumot beruvchi buyruqlar (soat, ob-havo, batareya…) bunga kirmaydi.
_VISUAL_HINTS = ("och", "ochib", "yop", "yopib", "ishga tushir", "yarat", "yasa",
                 "qo'y", "qoy", "pauza", "keyingi", "oldingi", "to'xtat",
                 "nusxa", "joylashtir", "kesib", "belgila", "yoz", "tahrir",
                 "kattalashtir", "kichiklashtir", "scroll", "sahifa",
                 "открой", "закрой", "создай", "запусти")


def is_visual_change(text):
    low = asistent._norm(text)
    return any(h in low for h in _VISUAL_HINTS)


def wants_network(text):
    """Foydalanuvchi tarmoqdagi qurilmalarni so'raganmi."""
    low = asistent._norm(text)
    return any(k in low for k in ("kim ulandi", "kim ulangan", "tarmoqda kim", "tarmoq holati",
                                  "qurilmalar", "tarmoqni skanerla", "tarmog", "wifi da kim",
                                  "kto podklyuchen", "ustройства"))


# ---------- Handlerlar ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id in AUTHORIZED:
        name = asistent._load_user_name()
        salom = ("Salom" + ((", " + name) if name else "") +
                 "! Men DODA. Menga buyruq bering (matn yoki ovoz).\n"
                 "🎛 /panel — tugmali boshqaruv\n📋 /buyruqlar — nimalar qila olishim\n"
                 "🔐 /ruxsat — macOS ruxsatlari\n🛠 /log — xatolar jurnali")
        await update.message.reply_text(salom)
    else:
        chat_id = update.effective_chat.id
        if load_owner() is None:
            await update.message.reply_text(
                "Salom! Men DODA.\n\n⚠️ Ega hali belgilanmagan. Xavfsizlik uchun ega FAQAT "
                "kompyuter terminali orqali belgilanadi.\n\n"
                "Sizning Telegram ID: %d\n"
                "Kompyuterда:  echo %d > ~/.doda_owner_id\n"
                "So'ng botni qayta ishga tushiring." % (chat_id, chat_id))
        else:
            await update.message.reply_text(
                "Salom! Men DODA. Bu bot faqat egasiga xizmat qiladi — "
                "sizga kirish ruxsati yo'q.")


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

    if chat_id not in AUTHORIZED:
        res = authorize_if_owner(chat_id)
        if res == "no_owner":
            # Ega hali belgilanmagan — FAQAT terminal orqali qo'lда belgilanadi (xavfsizlik)
            await update.message.reply_text(
                "⚠️ DODA egasi hali belgilanmagan.\n"
                "Xavfsizlik uchun ega FAQAT kompyuter terminali orqali belgilanadi "
                "(parol orqali emas).\n\n"
                "Sizning Telegram ID: %d\n\n"
                "Agar bu SIZning kompyuteringiz bo'lsa, terminalда bajaring:\n"
                "echo %d > ~/.doda_owner_id\n"
                "So'ng: launchctl kickstart -k gui/$(id -u)/com.doda.bot" % (chat_id, chat_id))
        elif res is True:
            await update.message.reply_text(
                "✅ Xush kelibsiz, ega! Menga buyruq bering — /panel bilan tugmali boshqaruv.")
        else:
            await update.message.reply_text(
                "⛔ Bu DODA boshqa egaga bog'langan. Kirishga ruxsat yo'q.")
            await _alert_owner_intrusion(context, chat_id, update)
        return

    # macOS ruxsatlarini tekshirish so'rovi
    if wants_permission(text):
        res = await asyncio.to_thread(ruxsatlar.check_all)
        rep = await asyncio.to_thread(ruxsatlar.report)
        kb = _ruxsat_keyboard(res) if any(v is False for v in res.values()) else None
        await update.message.reply_text(rep, parse_mode="Markdown", reply_markup=kb)
        return

    low = asistent._norm(text)   # quyidagi barcha tekshiruvlar uchun bir marta

    # 5 soniyalik video (rasmdan OLDIN — "video" so'zi bo'lsa)
    vkind = wants_video(text)
    if vkind:
        await _send_video(update, vkind)
        return

    # Ekran/kamera rasmini yuborish (masofadan ko'rish)
    kind = wants_image(text)
    if kind:
        await _send_capture(update, kind)
        return

    # Terminal buyrug'i — HAR DOIM tasdiqlash bilan (to'liq kompyuter boshqaruvi)
    cmd = extract_shell(text)
    if cmd:
        cid = secrets.token_hex(3)
        _pending_cmds[cid] = (chat_id, cmd)
        warn = "⚠️ *XAVFLI* buyruqqa o'xshaydi!\n\n" if is_dangerous(cmd) else ""
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Bajar", callback_data="run:" + cid),
            InlineKeyboardButton("❌ Bekor", callback_data="cancel:" + cid)]])
        await update.message.reply_text(
            warn + "Shu buyruqni bajaraymi?\n`" + cmd + "`",
            reply_markup=kb, parse_mode="Markdown")
        return

    # Telegram xabar yuborish — SKRINSHOT bilan tasdiqlab (noto'g'ri kontaktга ketmasin)
    if asistent._is_telegram_send(text):
        await _prepare_telegram(update, text)
        return

    # Wi-Fi'ni "uy tarmog'i" deb saqlash
    if any(k in low for k in ("uy deb saqla", "uy tarmogi deb", "uy wifi deb", "shu wifini uy",
                              "hozirgi wifini uy", "wifini uy", "uy qilib saqla")):
        ssid = await asyncio.to_thread(tarmoq.save_home)
        if ssid:
            await update.message.reply_text("🏠 Saqladim! «%s» endi uy Wi-Fi'si. "
                                            "Uydaman/uyda emasman va kim ulanganini shundan bilaman." % ssid)
        else:
            await update.message.reply_text("Wi-Fi nomini aniqlay olmadim (Wi-Fi yoqilganmi?).")
        return

    # Uy tarmog'i — kim ulangan / holat
    if wants_network(text):
        await update.message.reply_text("📡 Skanerlayapman...")
        summary = await asyncio.to_thread(lambda: (tarmoq.update(), tarmoq.summary())[1])
        await update.message.reply_text(summary)
        return

    # Takroriy eslatma (har kuni / ish kunlari / muayyan kunlar)
    if asistent.is_recurring(text):
        parsed = asistent.parse_recurring(text)
        if parsed:
            days, hh, mm, note = parsed
            asistent.add_recurring(chat_id, days, hh, mm, note)
            await update.message.reply_text(
                "✅ Takroriy eslatma: " + note + " — " + asistent._days_name(days) +
                " soat " + ("%02d:%02d" % (hh, mm)) + "."
            )
        else:
            await update.message.reply_text("Takroriy eslatma uchun kun va vaqtni ayting.")
        return

    # Eslatma -> belgilangan vaqtда Telegram orqali yetkazamiz
    if asistent.is_reminder(text):
        delay, note = asistent.parse_reminder(text)
        if delay is None:
            await update.message.reply_text(
                "Qachon eslatay? Masalan: «2 soatdan keyin majlis eslat» yoki «soat 15 da eslat»."
            )
        else:
            fire_ts = time.time() + delay
            _add_pending(chat_id, fire_ts, note)
            asyncio.create_task(_send_reminder(context.bot, chat_id, delay, note, fire_ts))
            await update.message.reply_text("✅ Eslatib qo'yaman: " + note + " — " + _human_delay(delay) + ".")
        return

    # Avto-skrin sozlamasi
    low = asistent._norm(text)
    if any(k in low for k in ("avto skrin", "avtoskrin", "avto ekran", "skrinni yoq", "ekranni avtomatik")):
        set_autoshot(True)
        await update.message.reply_text("✅ Avto-skrin yoqildi — endi biror narsa ochilsa/o'zgarsa, ekranни o'zim yuboraman.")
        return
    if any(k in low for k in ("avto skrinni ochir", "avtoskrin ochir", "skrinni ochir", "avto skrin ochir", "avto ekranni ochir")):
        set_autoshot(False)
        await update.message.reply_text("✅ Avto-skrin o'chirildi.")
        return

    def work():
        with _lock:
            return asistent.process_text(text)
    reply = await asyncio.to_thread(work)
    await update.message.reply_text(reply)

    # Vizual o'zgarish bo'lsa (ochish/yopish/tahrir) — natijani ekran rasmi bilan ko'rsatamiz
    if autoshot_on() and is_visual_change(text):
        logging.info("autoshot: '%s' uchun skrin olinyapti...", text)
        await asyncio.sleep(1.2)          # oyna ochilishini kutamiz
        try:
            await _send_capture(update, "screen", announce=False)
            logging.info("autoshot: skrin yuborildi")
        except Exception as e:
            logging.error("autoshot xato: %s", e)


async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»).")
        return

    tg_file = await (update.message.voice or update.message.audio).get_file()
    ogg = os.path.join(tempfile.gettempdir(), "doda_%s.ogg" % chat_id)
    wav = ogg[:-4] + ".wav"
    await tg_file.download_to_drive(ogg)

    def work():
        subprocess.run(["ffmpeg", "-y", "-i", ogg, "-ar", "16000", "-ac", "1", wav],
                       capture_output=True)
        text = ""
        try:
            text = transcribe_wav(wav)
        finally:
            for p in (ogg, wav):
                if os.path.exists(p):
                    os.remove(p)
        if not text:
            return "Ovozni tushunmadim, qayta urinib ko'ring."
        with _lock:
            return "🎤 " + text + "\n\n" + asistent.process_text(text)

    reply = await asyncio.to_thread(work)
    await update.message.reply_text(reply)


async def _prepare_telegram(update: Update, text):
    """Telegram xabarini TAYYORLAYDI (chatni ochib matnни qo'yadi, LEKIN yubormaydi),
    ekran suratini oladi va ✅Yubor/❌Bekor tugmalari bilan yuboradi. Foydalanuvchi KIM
    ochilganini KO'RIB tasdiqlagach yuboriladi (noto'g'ri kontaktга ketmaslik uchun)."""
    chat_id = update.effective_chat.id
    recipient, msg = asistent.parse_telegram_send(text)
    if not recipient or not msg:
        await update.message.reply_text(
            "Format: «telegramda <kim> ga <matn> yubor» deб yuboring.")
        return
    await update.message.reply_text("✍️ «%s» chatini ochyapman..." % recipient)

    # Chatni ochib matnni kiritamiz — YUBORMAYMIZ (do_send=False)
    ok = await asyncio.to_thread(asistent._send_telegram_ui, recipient, msg, False)
    if not ok:
        await update.message.reply_text(
            "❌ Telegramда tayyorlolmadim. Ilova ochiqmi va Accessibility ruxsati bormi tekshiring.")
        return
    await asyncio.sleep(0.6)   # oyna joylashsin

    # Ochilgan chatni ko'rsatish uchun ekran surati
    path = await asyncio.to_thread(vision.capture_screen)
    cid = secrets.token_hex(3)
    _pending_tg[cid] = (chat_id, recipient, msg)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Yubor", callback_data="tgok:" + cid),
        InlineKeyboardButton("❌ Bekor", callback_data="tgno:" + cid)]])
    caption = ("📨 *Yuborishga tayyor*\n\n👤 Kimga: *%s*\n💬 Matn: %s\n\n"
               "⚠️ Ochilgan chat TO'G'RImi? Skrinshotni tekshiring, so'ng tasdiqlang."
               % (recipient, msg))
    try:
        if path:
            with open(path, "rb") as f:
                await update.message.reply_document(
                    document=f, filename=os.path.basename(path),
                    caption=caption, parse_mode="Markdown", reply_markup=kb)
        else:
            await update.message.reply_text(
                caption + "\n\n(Ekran suratini ololmadim — baribir chatни tekshiring.)",
                parse_mode="Markdown", reply_markup=kb)
    finally:
        if path:
            try:
                os.remove(path)
            except Exception:
                pass


async def _send_capture(update: Update, kind, announce=True):
    """Ekran yoki kamera rasmini olib, Telegram'ga yuboradi."""
    if announce:
        await update.message.reply_text("📸 Olyapman...")

    def cap():
        return vision.capture_screen() if kind == "screen" else vision.capture_camera()

    path = await asyncio.to_thread(cap)
    if not path:
        # Aniq sabab: ruxsatni shu jarayonda tekshiramiz
        kk = "screen" if kind == "screen" else "camera"
        ok, hint = await asyncio.to_thread(ruxsatlar.ensure_or_hint, kk)
        if not ok:
            msg = ("❌ " + hint +
                   "\n\nRuxsat berilishi kerak bo'lgan ilova:\n`%s`\n\n"
                   "Yoqgach «botni qayta ishga tushir» deng." % ruxsatlar.python_path())
            kb = _ruxsat_keyboard({kk: False})
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=kb)
        else:
            await update.message.reply_text(
                "❌ %s ololmadim (ruxsat bor ko'rinadi — qurilma band bo'lishi mumkin)."
                % ("Ekranni" if kind == "screen" else "Kamerani"))
        return
    try:
        with open(path, "rb") as f:
            if kind == "screen":
                # HUJJAT sifatida -> Telegram siqmaydi, matn tiniq qoladi
                await update.message.reply_document(
                    document=f, filename=os.path.basename(path), caption="🖥 Ekran (tiniq)")
            else:
                await update.message.reply_photo(photo=f, caption="📷 Kamera")
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


async def _send_video(update: Update, kind, seconds=5):
    """Ekran yoki kameradan 5 soniyalik video olib, Telegram'ga yuboradi."""
    await update.message.reply_text("🎬 %d soniyalik %s videosi olinyapti..."
                                    % (seconds, "kamera" if kind == "camera" else "ekran"))

    def rec():
        return (vision.record_camera(seconds) if kind == "camera"
                else vision.record_screen(seconds))

    path = await asyncio.to_thread(rec)
    if not path:
        hint = ("Kamera ruxsati kerak (Privacy → Camera)." if kind == "camera"
                else "Ekran yozish ruxsati kerak (Privacy → Screen Recording).")
        await update.message.reply_text("❌ Video ololmadim. " + hint)
        return
    try:
        with open(path, "rb") as f:
            await update.message.reply_video(
                video=f, caption=("📷 Kamera videosi" if kind == "camera" else "🖥 Ekran videosi"))
    except Exception:
        # video sifatida yuborilmasa, hujjat sifatida
        try:
            with open(path, "rb") as f:
                await update.message.reply_document(document=f, filename=os.path.basename(path))
        except Exception as e:
            await update.message.reply_text("❌ Videoni yuborib bo'lmadi: " + str(e))
    finally:
        try:
            os.remove(path)
        except Exception:
            pass


def _panel_keyboard():
    """Boshqaruv panel tugmalari (inline)."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Ekran", callback_data="p:screen"),
         InlineKeyboardButton("🎬 Video", callback_data="p:video")],
        [InlineKeyboardButton("📸 Kamera", callback_data="p:camera"),
         InlineKeyboardButton("💻 Holat", callback_data="p:status")],
        [InlineKeyboardButton("📡 Tarmoq", callback_data="p:network"),
         InlineKeyboardButton("📋 Loglar", callback_data="p:logs")],
        [InlineKeyboardButton("🌐 Dashboard", callback_data="p:dash"),
         InlineKeyboardButton("🔄 Botni restart", callback_data="p:restart")],
        [InlineKeyboardButton("🔐 Ruxsatlar", callback_data="p:ruxsat")],
    ])


TUNNEL_URL_FILE = os.path.expanduser("~/.doda_tunnel_url")


def _tunnel_url():
    try:
        u = open(TUNNEL_URL_FILE).read().strip()
        return u if u.startswith("https://") else ""
    except FileNotFoundError:
        return ""


def _web_token():
    try:
        return open(os.path.expanduser("~/.doda_web_token")).read().strip()
    except Exception:
        return ""


def _tunnel_url_tok():
    """Tunnel URL + maxfiy token qo'shilgan (masalan https://doda.doda-ai.uz/?t=XXX).
    Mini App ichida /api chaqiruvlari ishonchli auth'дан o'tishi uchun — initData
    Telegram webview'да ba'zan ishlamaydi, token esa doim ishlaydi. Token faqat egaга
    yuborilgan tugmада bo'ladi (bot xabari kabi maxfiy)."""
    u = _tunnel_url()
    t = _web_token()
    return (u + "/?t=" + t) if (u and t) else u


def _url_alive(u):
    """URL ochilayaptimi (tez tekshiruv). GET ishlatamiz — dashboard serveri HEAD'ни
    qo'llamaydi (501 qaytaradi), shu sabab HEAD bilan tirik tunnel ham 'o'lik' ko'rinardi."""
    if not u:
        return False
    try:
        with urllib.request.urlopen(u + "/", timeout=8) as r:
            return r.status < 500
    except urllib.error.HTTPError:
        return True   # server javob berdi (4xx ham) -> tunnel TIRIK
    except Exception:
        return False


def _lan_url():
    """Uy Wi-Fi'да telefon brauzerида ochiladigan havola (tunnel SHART EMAS)."""
    try:
        tok = open(os.path.expanduser("~/.doda_web_token")).read().strip()
    except Exception:
        return ""
    ip = ""
    for iface in ("en0", "en1"):
        try:
            ip = subprocess.run(["ipconfig", "getifaddr", iface],
                                capture_output=True, text=True, timeout=5).stdout.strip()
            if ip:
                break
        except Exception:
            pass
    return ("http://%s:8765/?t=%s" % (ip, tok)) if ip else ""


async def cmd_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """DODA'ni to'liq Mini App (web dashboard) sifatida ochadigan tugma + LAN zaxira havola."""
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»).")
        return
    url = _tunnel_url()
    alive = await asyncio.to_thread(_url_alive, url)
    lan = await asyncio.to_thread(_lan_url)

    if url and alive:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎙️ DODA'ni ochish", web_app=WebAppInfo(url=_tunnel_url_tok()))]])
        txt = ("🎙️ *DODA Mini App* — to'liq boshqaruv paneli.\n"
               "Tugmani bosing (faqat sizning hisobingiz kira oladi).")
        if lan:
            txt += "\n\n🏠 *Uy Wi-Fi'да* (ishonchliroq, tunnel'siz) — brauzerda oching:\n" + lan
        await update.message.reply_text(txt, reply_markup=kb, parse_mode="Markdown")
    else:
        # Tunnel o'lik/tayyor emas -> yangilaymiz va LAN havolани beramiz
        try:
            subprocess.run(["launchctl", "kickstart", "-k",
                            "gui/%d/com.doda.tunnel" % os.getuid()], capture_output=True)
        except Exception:
            pass
        msg = ("⚠️ Mini App tunneli hozir javob bermayapti (vaqtinchalik tarmoq uzilishi bo'lishi mumkin). "
               "Yangiladim — ~20 soniyadan so'ng «/app» ni QAYTA yuboring.")
        if lan:
            msg += ("\n\n🏠 *Hoziroq ishlaydigan yo'l* — uy Wi-Fi'да telefon brauzerида oching "
                    "(tunnel shart emas):\n" + lan)
        await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»).")
        return
    await update.message.reply_text("🎙️ *DODA boshqaruv paneli*\nKerakli tugmani bosing:",
                                    reply_markup=_panel_keyboard(), parse_mode="Markdown")


async def cmd_buyruqlar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»).")
        return
    await update.message.reply_text(build_menu(), parse_mode="Markdown")


async def cmd_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        return
    # Avval tuzalган (eski) xatolarni avtomatik olib tashlaymiz
    kept, pruned = prune_errors(30)
    tozalandi = ("🧹 %d ta eski (tuzalgan) xato avtomatik o'chirildi.\n\n" % pruned) if pruned else ""
    # FAQAT markaziy jurnal (ERRORS_LOG). Faol xato bo'lmasa, bot_error.log'даги
    # zararsiz network-traceback'larni KO'RSATMAYMIZ (chalkashlik bo'lmasin).
    tail = read_log_tail(ERRORS_LOG, 25) if kept > 0 else ""
    if kept > 0 and tail:
        text = tozalandi + "🧾 Hozirgi xatolar (%d):\n\n%s" % (kept, tail)
    else:
        text = tozalandi + "✅ Faol xato yo'q — hammasi joyida.\n(Internet uzilishi kabi vaqtinchalik xatolar bu yerда ko'rsatilmaydi — DODA ularni o'zi eplaydi.)"
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🧹 Hammasini tozalash", callback_data="log_clean")]])
    await update.message.reply_text(text[-3900:], reply_markup=kb)


def _ruxsat_keyboard(res):
    """Yetishmayotgan ruxsatlar uchun «bo'limni ochish» tugmalari (Mac ekranida ochiladi)."""
    rows = []
    labels = {"screen": "🖥 Screen Recording", "accessibility": "♿️ Accessibility",
              "fulldisk": "💽 Full Disk Access", "camera": "📷 Camera"}
    for k, v in res.items():
        if v is False:
            rows.append([InlineKeyboardButton("⚙️ " + labels[k] + " ni ochish",
                                              callback_data="rux:" + k)])
    rows.append([InlineKeyboardButton("🔄 Qayta tekshirish", callback_data="rux:recheck")])
    return InlineKeyboardMarkup(rows)


async def cmd_ruxsat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """macOS ruxsatlarini shu bot jarayonida tekshirib, aniq yo'l ko'rsatadi."""
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»).")
        return
    res = await asyncio.to_thread(ruxsatlar.check_all)
    text = await asyncio.to_thread(ruxsatlar.report)
    kb = _ruxsat_keyboard(res) if any(v is False for v in res.values()) else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


def wants_permission(text):
    low = asistent._norm(text)
    return any(k in low for k in ("ruxsat", "ruxsatlar", "permission", "razreshenie",
                                  "dostup", "ruxsatni tekshir", "ruxsatlarni tekshir"))


# ---------- To'g'ridan-to'g'ri buyruqlar ("/" menyusidan tez foydalanish uchun) ----------
async def cmd_ekran(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»)."); return
    await _send_capture(update, "screen")


async def cmd_kamera(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»)."); return
    await _send_capture(update, "camera")


async def cmd_holat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»)."); return
    await update.message.reply_text("💻 " + await asyncio.to_thread(mac_system.report))


async def cmd_tarmoq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id not in AUTHORIZED:
        await update.message.reply_text("Avval parol yuboring (kompyuterda «parol ber»)."); return
    s = await asyncio.to_thread(lambda: (tarmoq.update(), tarmoq.summary())[1])
    await update.message.reply_text(s)


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.message.chat.id not in AUTHORIZED:
        await q.answer("Ruxsat yo'q")
        return
    if q.data == "log_clean":
        clean_logs()
        await q.answer("Tozalandi ✅")
        await q.edit_message_text("🧹 Loglar tozalandi — xatolar tarixi o'chirildi.")
        return

    # Ruxsat bo'limini ochish / qayta tekshirish
    if q.data.startswith("rux:"):
        what = q.data[4:]
        if what == "recheck":
            await q.answer("Tekshirilyapti…")
            res = await asyncio.to_thread(ruxsatlar.check_all)
            text = await asyncio.to_thread(ruxsatlar.report)
            kb = _ruxsat_keyboard(res) if any(v is False for v in res.values()) else None
            await q.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)
        else:
            ok = await asyncio.to_thread(ruxsatlar.open_settings, what)
            await q.answer("Mac ekranida ochildi" if ok else "Ochib bo'lmadi")
            await q.message.reply_text(
                "⚙️ Sozlamalar bo'limi Mac ekranida ochildi.\n"
                "Ro'yxatga bu ilovani qo'shing va yoqing:\n`%s`\n\n"
                "Yoqgach «botni qayta ishga tushir» deng, so'ng /ruxsat bilan tekshiring."
                % ruxsatlar.python_path(), parse_mode="Markdown")
        return

    # Boshqaruv panel tugmalari
    if q.data.startswith("p:"):
        action = q.data[2:]
        await q.answer("Bajarilyapti…")
        if action == "screen":
            await _send_capture(q, "screen", announce=False)
        elif action == "camera":
            await _send_capture(q, "camera", announce=False)
        elif action == "video":
            await _send_video(q, "screen")
        elif action == "status":
            await q.message.reply_text("💻 " + await asyncio.to_thread(mac_system.report))
        elif action == "network":
            s = await asyncio.to_thread(lambda: (tarmoq.update(), tarmoq.summary())[1])
            await q.message.reply_text(s)
        elif action == "logs":
            kept, pruned = prune_errors(30)
            tail = read_log_tail(ERRORS_LOG, 20)
            await q.message.reply_text(("🧾 Xatolar (%d):\n\n%s" % (kept, tail)) if tail
                                       else "✅ Faol xato yo'q.")
        elif action == "dash":
            try:
                tok = open(os.path.expanduser("~/.doda_web_token")).read().strip()
                ip = subprocess.run(["ipconfig", "getifaddr", "en0"],
                                    capture_output=True, text=True).stdout.strip() or "localhost"
                await q.message.reply_text("🌐 Dashboard havolasi:\nhttp://%s:8765/?t=%s\n"
                                           "(maxfiy — boshqaga bermang)" % (ip, tok))
            except Exception:
                await q.message.reply_text("Dashboard havolasini olib bo'lmadi.")
        elif action == "restart":
            subprocess.run(["launchctl", "kickstart", "-k",
                            "gui/%d/com.doda.bot" % os.getuid()], capture_output=True)
            await q.message.reply_text("🔄 Bot qayta ishga tushirilyapti…")
        elif action == "ruxsat":
            res = await asyncio.to_thread(ruxsatlar.check_all)
            rep = await asyncio.to_thread(ruxsatlar.report)
            kb = _ruxsat_keyboard(res) if any(v is False for v in res.values()) else None
            await q.message.reply_text(rep, parse_mode="Markdown", reply_markup=kb)
        return

    # Telegram xabarini tasdiqlash / bekor qilish (skrinshotni ko'rgach)
    if q.data.startswith(("tgok:", "tgno:")):
        action, cid = q.data.split(":", 1)
        async def _tg_result(txt):
            # xabar hujjat (caption) yoki oddiy matn bo'lishi mumkin — ikkalasiga ham chidamli
            try:
                await q.edit_message_caption(txt)
            except Exception:
                try:
                    await q.edit_message_text(txt)
                except Exception:
                    await q.message.reply_text(txt)
        pend = _pending_tg.pop(cid, None)
        if not pend:
            await q.answer("Muddati o'tgan")
            await _tg_result("⏳ Bu so'rov eskirgan, qayta yuboring.")
            return
        _, recipient, msg = pend
        if action == "tgno":
            await q.answer("Bekor qilindi")
            await asyncio.to_thread(asistent._telegram_cancel_send)
            await _tg_result("❌ Bekor qilindi — «%s» ga yuborilmadi." % recipient)
            return
        await q.answer("Yuborilyapti…")
        sent = await asyncio.to_thread(asistent._telegram_confirm_send)
        await _tg_result(("✅ «%s» ga yuborildi:\n💬 %s" % (recipient, msg)) if sent
                         else "⚠️ Yuborolmadim — chat ochiqmi tekshiring.")
        return

    # Terminal buyrug'ini tasdiqlash / bekor qilish
    if q.data.startswith(("run:", "cancel:")):
        action, cid = q.data.split(":", 1)
        pend = _pending_cmds.pop(cid, None)
        if not pend:
            await q.answer("Muddati o'tgan")
            await q.edit_message_text("⏳ Bu so'rov eskirgan, qayta yuboring.")
            return
        _, cmd = pend
        if action == "cancel":
            await q.answer("Bekor qilindi")
            await q.edit_message_text("❌ Bekor qilindi: `" + cmd + "`", parse_mode="Markdown")
            return
        await q.answer("Bajarilyapti...")
        await q.edit_message_text("⏳ Bajarilyapti: `" + cmd + "`", parse_mode="Markdown")
        out, code = await asyncio.to_thread(run_shell, cmd)
        belgi = "✅" if code == 0 else "⚠️ (kod %s)" % code
        matn = belgi + " `" + cmd + "`\n\n```\n" + out[:3500] + "\n```"
        await q.message.reply_text(matn, parse_mode="Markdown")


# Xato bildirishnomasi (bir xil xato bilan bezovta qilmaslik uchun cheklangan)
_last_alert = [0.0]


async def on_error(update, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    transient = isinstance(err, (NetworkError, TimedOut))
    if transient:
        logging.warning("Tarmoq uzilishi: %s", type(err).__name__)
    else:
        logging.error("DODA xatosi: %s", err, exc_info=err)
    # Markaziy jurnalga FAQAT haqiqiy (o'tkinchi bo'lmagan) xatolarни yozamiz.
    # NetworkError/TimedOut — DNS blip kabi o'z-o'zidan tuzaladigan shovqin; /log ni
    # va diskни ifloslamasin (faqat logging.warning'да qoladi).
    if not transient:
        try:
            import traceback as _tb
            with open(ERRORS_LOG, "a", encoding="utf-8") as f:
                f.write("%s [bot] %s: %s\n" %
                        (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), type(err).__name__, err))
                f.write("".join(_tb.format_exception(type(err), err, err.__traceback__)) + "\n")
        except Exception:
            pass
    now = time.time()
    if now - _last_alert[0] < 120:      # 2 daqiqada bir martadan ko'p yubormaymiz
        return
    _last_alert[0] = now
    turi = "Tarmoq uzilishi" if isinstance(err, (NetworkError, TimedOut)) else "Xatolik"
    msg = "⚠️ " + turi + ": " + type(err).__name__ + "\n/log — batafsil ko'rish."
    for uid in list(AUTHORIZED):
        try:
            await context.bot.send_message(chat_id=uid, text=msg)
        except Exception:
            pass


_LOCK_FILE = "/tmp/doda_bot.lock"
_lock_handle = None


def acquire_single_instance():
    """Faqat bitta bot ishlashini ta'minlaydi (Conflict oldini oladi)."""
    global _lock_handle
    _lock_handle = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(_lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def main():
    if not acquire_single_instance():
        print("ℹ️  DODA bot ALLAQACHON ishlab turibdi (24/7 xizmat orqali).\n"
              "   Uni qo'lда ishga tushirish shart emas — Telegramда @voice_doda_bot ga yozavering.")
        return
    try:
        asistent._cleanup_temp_files()   # oldingi ishdan qolган vaqtinchalik fayllarni tozalaymiz
    except Exception:
        pass
    token = load_token()
    if not token:
        print("❌ Token topilmadi!\n"
              "   echo \"TOKEN\" > ~/.doda_bot_token && chmod 600 ~/.doda_bot_token\n"
              "   yoki:  export TELEGRAM_BOT_TOKEN=\"...\"")
        return
    if not validate_token(token):
        # Yaroqsiz token: kutubxonaga bermaymiz -> traceback ham, token ham logga tushmaydi
        print("❌ Token yaroqsiz yoki bekor qilingan. @BotFather'dan yangi token oling "
              "va ~/.doda_bot_token ga yozing.")
        return
    app = (Application.builder().token(token)
           .post_init(_post_init).post_shutdown(_shutdown).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("app", cmd_app))
    app.add_handler(CommandHandler("panel", cmd_panel))
    app.add_handler(CommandHandler("buyruqlar", cmd_buyruqlar))
    app.add_handler(CommandHandler("log", cmd_log))
    app.add_handler(CommandHandler("ruxsat", cmd_ruxsat))
    app.add_handler(CommandHandler("ekran", cmd_ekran))
    app.add_handler(CommandHandler("kamera", cmd_kamera))
    app.add_handler(CommandHandler("holat", cmd_holat))
    app.add_handler(CommandHandler("tarmoq", cmd_tarmoq))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, on_voice))
    app.add_error_handler(on_error)
    print("✅ DODA bot ishga tushdi. To'xtatish: Ctrl+C")
    app.run_polling()


if __name__ == "__main__":
    main()
