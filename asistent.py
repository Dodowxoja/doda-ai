import os
import re
import json
import time
import difflib
import random
import socket
import asyncio
import tempfile
import threading
import traceback
import webbrowser
import subprocess
import urllib.parse
import urllib.request

import datetime as dt

import edge_tts
import speech_recognition as sr

from buyruq_baza import APPS, SITES, FOLDERS, SEARCH_ENGINES, KOMANDALAR
import buyruq_baza as buyruq_baza
import foydalanuvchi as foydalanuvchi
import mac_system as mac_system  # batareya/CPU/RAM/bufer holati

# Ovoz jinsi (erkak/ayol) — faylдan yuklanadi, "ayol ovoz"/"erkak ovoz" buyrug'i bilan almashtiriladi
VOICE_FILE = os.path.expanduser("~/.doda_voice")
try:
    VOICE_GENDER = open(VOICE_FILE).read().strip() if os.path.exists(VOICE_FILE) else "male"
    if VOICE_GENDER not in ("male", "female"):
        VOICE_GENDER = "male"
except Exception:
    VOICE_GENDER = "male"

# --- Ovoz-tanish (STT) sozlamalari ---
INPUT_MODE = "wake"             # "wake" = uyg'otkich so'z rejimi (jimlikда tinglamaydi;
                                # «Doda» desangiz uyg'onadi va «labbay» deydi).
                                # "hybrid" = ovoz+matn, "voice" = doim mikrofon, "text" = faqat klaviatura.
                                # Telegram bot alohida ishlaydi (bu sozlama faqat desktopga ta'sir qiladi).
LISTEN_TIMEOUT = 6             # hybrid: shu soniya ichida gapirmasangiz, matn yozish so'raladi

# --- Uyg'otkich so'z (wake word) rejimi sozlamalari ---
WAKE_WORDS = ["doda", "дода", "dada", "дада", "toda", "тода", "додо"]  # STT xatolarига bardoshli
WAKE_REPLIES = ["Labbay!", "Eshitaman.", "Xizmatingizdaman.", "Ha, labbay.", "Shundaymi, tinglayman."]
WAKE_LISTEN_TIMEOUT = 5        # bitta tinglash oynasi (soniya). Jimlik bo'lsa ishlov bermay qayta kutadi.
WAKE_PHRASE_LIMIT = 4         # «Doda» iborasi qisqa — shuncha soniya yoziladi
WAKE_SESSION_SILENCE = 10     # «Doda» degach suhbat davom etadi; shuncha soniya JIM bo'lsangiz — tinglashni bas qiladi
RECOGNITION_LANGS = ["uz-UZ", "ru-RU"]  # Online (Google) uchun nomzod tillar (faqat o'zbek va rus).
                                         # Confidence bo'yicha eng yaxshisi tanlanadi.
                                         # Ingliz o'chirilgan; kerak bo'lsa "en-US" ni qayta qo'shasiz.
WHISPER_MODEL_SIZE = "medium"  # Offline (Whisper): tiny/base/small/medium.
                                # O'zbek tili uchun "medium" tavsiya etiladi (sekinroq lekin aniqroq).
WHISPER_LANG = "uz"            # Offline til: "uz" (majburiy o'zbek), yoki None (avtomatik aniqlash).
                                # Asosan o'zbekcha gapirsangiz "uz" qoldiring; rus uchun None qiling.
PHRASE_TIME_LIMIT = 8          # Bir gap uchun maksimal yozish vaqti (soniya).

# --- AI erkin suhbat (Claude API) sozlamalari ---
# API kaliti KODDA SAQLANMAYDI. Ikki joydan biridan olinadi (birinchisi topilsa o'sha):
#   1) muhit o'zgaruvchisi:  export ANTHROPIC_API_KEY="sk-ant-..."
#   2) maxfiy fayl (24/7 bot uchun qulay):
#        echo -n 'sk-ant-...' > ~/.doda_claude_key && chmod 600 ~/.doda_claude_key
CLAUDE_KEY_FILE = "~/.doda_claude_key"   # kalit shu faylda bo'lsa avtomatik o'qiladi
AI_CHAT_ENABLED = True          # AI suhbat YOQILGANMI? Kredit qo'shgach True qiling.
                                # False bo'lsa Claude'ga umuman bormaydi.
CHAT_MODEL = "claude-haiku-4-5" # Arzon va tez model (ovozli suhbat uchun yetarli).
                                # Kuchliroq xohlasangiz: "claude-opus-5" yoki "claude-sonnet-5"
CHAT_MAX_TOKENS = 1024          # Bitta javob uchun maksimal token (ovoz uchun qisqa yetadi)
CHAT_HISTORY_LIMIT = 20         # Suhbat tarixida saqlanadigan oxirgi xabarlar soni (kontekst uchun)
CHAT_SYSTEM_PROMPT = (
    "Sening isming DODA — Muhammadxo'ja yaratgan shaxsiy ovozli yordamchi. "
    "HAR DOIM O'ZBEK TILIDA javob ber. Faqat foydalanuvchi ANIQ rus tilida (kirill "
    "harflar bilan) yozsa, o'shanda rus tilida javob ber. INGLIZ TILIDA HECH QACHON "
    "javob berma — foydalanuvchining so'zlari ingliz tiliga o'xshab ketsa yoki noto'g'ri "
    "tanilgan bo'lsa ham, javobing DOIM toza o'zbekcha bo'lsin. "
    "Javoblaring ovoz orqali o'qib eshittiriladi, shuning uchun QISQA, tabiiy va suhbatdosh bo'l. "
    "Markdown, ro'yxat belgilari, emoji yoki maxsus formatlash ISHLATMA — faqat oddiy gaplar. "
    "Mavzu bo'yicha chuqurroq so'ralsa, aniq va foydali tushuntir, lekin ortiqcha cho'zma."
)

# --- AI agent (kod/fayl bilan ishlash) sozlamalari ---
# Agent rejimi: Claude asboblardan (fayl o'qi/yoz/tahrirla, terminal, qidiruv) foydalanib
# haqiqiy ishlarni bajaradi. Asboblar agent_tools.py da. Kredit qo'shilgach True qiling.
AGENT_MODE_ENABLED = True        # Agent rejimi YOQILGANMI? (kredit + AI_CHAT_ENABLED kerak)
AGENT_MODEL = "claude-sonnet-5"  # Kod ishlari uchun: sifat/narx muvozanati.
                                 # Qiyin ishlar uchun "claude-opus-5", arzon uchun "claude-haiku-4-5"
AGENT_MAX_TOKENS = 8000          # Agent javoblari uzunroq bo'lishi mumkin (kod, fayl mazmuni)
AGENT_WORKSPACE = "~/Code"       # Agent SHU papka ichida ishlaydi (tashqariga chiqolmaydi)
AGENT_MAX_STEPS = 20             # Bitta so'rovda maksimal asbob-chaqiruv qadamlari (cheksiz aylanmaslik)
# Agent so'rovini aniqlaydigan kalit so'zlar (shular bo'lsa oddiy suhbat emas, agent ishlaydi)
AGENT_TRIGGERS = [
    "agent", "kod yoz", "kod yozib", "dastur yoz", "dastur yasa", "faylni", "faylga",
    "fayl yarat", "fayl o'qi", "papkada", "papkani", "loyihada", "loyihamda", "loyihani",
    "loyiha yarat", "loyiha yasa", "terminalda", "buyruqni bajar", "git ", "qidirib top",
    "kodni tuzat", "xatoni top", "xatoni tuzat", "test qil", "ishga tushir",
    # Tabiiy "yasab ber / yaratib ber" iboralari (foydalanuvchi shunday gapiradi)
    "yaratib ber", "yasab ber", "yozib ber", "yasa", "web yarat", "sayt yasa", "sayt yarat",
    "web sahifa", "veb sahifa", "portfolio", "flutter", "html", "css", "react",
    "ishni boshla", "boshla ishni", "kodni yoz", "ilova yasa", "ilova yarat",
]
AGENT_SYSTEM_PROMPT = (
    "Sening isming DODA — Muhammadxo'ja yaratgan shaxsiy yordamchi va kod agenti. "
    "Senga fayllar bilan ishlash va terminal buyruqlarini bajarish uchun asboblar berilgan. "
    "MUHIM: sen ALLAQACHON ~/Code papkasi ICHIDA ishlayapsan — bu sening ish papkang (workspace). "
    "Barcha yo'llar shu papkaga NISBATAN yoziladi. Foydalanuvchi «Code papkasida yarat» desa, "
    "bu shунчаki shu ish papkang demakdir — «Code/» prefiksini QO'SHMA. "
    "Masalan «Code ichida test_portfolio yarat» -> to'g'ri yo'l: «test_portfolio/main.dart» "
    "(NOTO'G'RI: «Code/test_portfolio/main.dart» — bu ~/Code/Code/... bo'lib ketadi). "
    "Foydalanuvchi topshirig'ini bajarish uchun asboblardan foydalanib ish qil: "
    "avval kerakli faylni read_file bilan o'qi, keyin edit_file yoki write_file bilan o'zgartir, "
    "kerak bo'lsa run_command bilan tekshir yoki ishga tushir. "
    "Har bir qadamdan oldin nima qilayotganingni qisqa tushuntir. "
    "Ish tugagach, natijani O'ZBEK tilida QISQA va sodda xulosa qilib ayt — "
    "QAYSI fayl(lar)ni QAYSI yo'lda yaratganingni ANIQ ayt "
    "(bu ovoz orqali ham eshittirilishi mumkin). Markdown yoki emoji ishlatma."
)

VOICES = {
    "male": {
        "uz": "uz-UZ-SardorNeural",
        "ru": "ru-RU-DmitryNeural",
        "en": "en-US-GuyNeural",
    },
    "female": {
        "uz": "uz-UZ-MadinaNeural",
        "ru": "ru-RU-SvetlanaNeural",
        "en": "en-US-JennyNeural",
    },
}

# --- Hissiyot (emotion) presetlari ---
# Ohang (pitch), tezlik (rate) va balandlik (volume) ni sozlab hissiyotni taqlid qilamiz.
# O'zbek ovozida ham ishlaydi. "neutral" = odatiy (o'zgarishsiz).
EMOTIONS = {
    "neutral":  {"rate": "+0%",  "pitch": "+0Hz",  "volume": "+0%"},   # odatiy
    "hursand":  {"rate": "+22%", "pitch": "+32Hz", "volume": "+13%"},   # xursand, quvonchli (yanada quvnoq)
    "hayajon":  {"rate": "+25%", "pitch": "+35Hz", "volume": "+15%"},   # hayajonli (excited)
    "hafa":     {"rate": "-15%", "pitch": "-25Hz", "volume": "-8%"},    # g'amgin, xafa
    "jahl":     {"rate": "+18%", "pitch": "+5Hz",  "volume": "+22%"},   # jahli chiqqan
    "xotirjam": {"rate": "-12%", "pitch": "-8Hz",  "volume": "+0%"},    # tinch, hamdard
}
EMOTION_FILE = os.path.expanduser("~/.doda_emotion")
try:
    CURRENT_EMOTION = open(EMOTION_FILE).read().strip() if os.path.exists(EMOTION_FILE) else "neutral"
    if CURRENT_EMOTION not in EMOTIONS:
        CURRENT_EMOTION = "neutral"
except Exception:
    CURRENT_EMOTION = "neutral"


_recognizer = sr.Recognizer()
# Google STT javob bermasa/tarmoq beqaror bo'lsa 6s da uziladi — aks holda wake-loop
# butunlay osilib qolardi (eng muhim tuzatish: ilgari _recognize_online cheksiz bloklanardi).
_recognizer.operation_timeout = 6
_whisper_model = None  # birinchi offline chaqiruvda yuklanadi (lazy-load)


def _has_internet(host="8.8.8.8", port=53, timeout=2):
    """Internet bor-yo'qligini tez tekshiradi (DNS portiga ulanib ko'radi)."""
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        return True
    except OSError:
        return False


def _get_whisper():
    """Whisper modelini bir marta yuklab, keshda saqlaydi."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print("Whisper modeli yuklanmoqda (birinchi marta biroz vaqt oladi)...")
        _whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
    return _whisper_model


def _recognize_online(audio):
    """Google orqali tanish. Tillar ro'yxati tartibida (o'zbek birinchi) —
    birinchi bo'sh bo'lmagan natijani qaytaradi. Shu sabab o'zbekcha afzal ko'riladi."""
    for lang in RECOGNITION_LANGS:
        try:
            result = _recognizer.recognize_google(audio, language=lang, show_all=True)
        except sr.UnknownValueError:
            continue
        if not result:
            continue
        text = result.get("alternative", [{}])[0].get("transcript", "").strip()
        if text:
            return text
    return ""


# Whisper jimlik/shovqinда shu kabi soxta iboralarni chiqaradi (mashhur nuqson) -> e'tiborsiz qoldiramiz
_WHISPER_HALLUCINATIONS = {
    "thanks for watching", "thank you for watching", "please subscribe",
    "subscribe", "thank you", "thanks", "you", "bye", "so", "okay",
    "спасибо за просмотр", "продолжение следует", "субтитры", "субтитры а",
    "редактор субтитров", "субтитры создавал", "amara.org", "субтитры делал",
}


def _recognize_offline(audio, for_wake=False):
    """faster-whisper orqali offline tanish. Til avtomatik aniqlanadi (uz/ru).
    for_wake=True — «Doda» kabi QISQA so'z uchun: VAD-filtri o'chiriladi (qisqa so'zni
    kesib tashlamasin) va til majburlanmaydi (avtomatik) — aks holda bo'sh qaytardi."""
    model = _get_whisper()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(audio.get_wav_data())
        wav_path = f.name
    try:
        segments, _info = model.transcribe(
            wav_path,
            language=None if for_wake else WHISPER_LANG,
            beam_size=1,
            vad_filter=not for_wake,            # jimlikni o'tkazib yuboradi; wake'da o'chiriladi
            condition_on_previous_text=False,
        )
        text = " ".join(seg.text for seg in segments).strip()
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
    # Soxta iboralarni filtrlaymiz -> bo'sh qaytaramiz (dastur qayta tinglaydi)
    if text.lower().strip(" .,!?…") in _WHISPER_HALLUCINATIONS:
        return ""
    return text


def listen():
    # Faqat klaviatura rejimi
    if INPUT_MODE == "text":
        return input("⌨️  Yozing: ")

    # Mikrofondan ovoz yozib olish
    with sr.Microphone() as source:
        _recognizer.adjust_for_ambient_noise(source, duration=0.3)
        if INPUT_MODE == "hybrid":
            print("🎤 Tinglayapman... (gapirmasangiz, Enter bosib yozishingiz mumkin)")
            try:
                audio = _recognizer.listen(
                    source, timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT
                )
            except sr.WaitTimeoutError:
                # Belgilangan vaqtда gapirilmadi -> matn yozishga o'tamiz
                return input("⌨️  Yozing: ")
        else:  # "voice"
            print("🎤 Tinglayapman...")
            audio = _recognizer.listen(source, phrase_time_limit=PHRASE_TIME_LIMIT)

    # Avval online (Google) — o'zbek/rus uchun ancha aniq. Ishlamasa -> offline (Whisper).
    try:
        text = _recognize_online(audio)
        if text:
            print("Siz (online):", text)
            return text
    except sr.RequestError:
        pass  # internet yo'q / xizmat javob bermadi -> offline'ga o'tamiz

    text = _recognize_offline(audio)
    if text:
        print("Siz (offline):", text)
    return text


_capture = None  # agar list bo'lsa, say() matnni shu yerga yig'adi (bot uchun, ovozsiz)


def say(text, lang="ru", emotion=None):
    # Bot rejimi: ovoz o'rniga matnni yig'amiz
    if _capture is not None:
        _capture.append(text)
        print("Doda:", text)
        return
    lang_voices = VOICES.get(VOICE_GENDER, VOICES["male"])
    voice = lang_voices.get(lang, lang_voices["ru"])
    # Hissiyot: berilmasa, joriy (saqlangan) hissiyotni ishlatamiz
    emo = emotion or CURRENT_EMOTION
    params = EMOTIONS.get(emo, EMOTIONS["neutral"])
    # Vaqtinchalik audioni yoziladigan vaqtinchalik papkaga saqlaymiz
    # (loyiha papkasi read-only bo'lishi mumkin).
    unique_filename = os.path.join(
        tempfile.gettempdir(), "doda_audio_" + str(random.randint(0, 10 ** 7)) + ".mp3"
    )

    # Save VA play — ikkalasi ham try/finally ичида: xato bo'lsa ham vaqtinchalik
    # fayl HAR DOIM o'chiriladi (diskда "musor" yig'ilmasin).
    try:
        asyncio.run(edge_tts.Communicate(text, voice, **params).save(unique_filename))
        # macOS'ning o'rnatilgan audio pleyeri (qo'shimcha kutubxona kerak emas)
        subprocess.run(["afplay", unique_filename])
    finally:
        try:
            if os.path.exists(unique_filename):
                os.remove(unique_filename)
        except OSError:
            pass

    print("Doda:", text)


def tts_bytes(text, lang="uz", emotion=None):
    """Matnни ovozga aylantirib, mp3 BAYTlarini qaytaradi (ijro ETMAYDI, afplay yo'q).
    Web dashboard uchun: brauzer bu baytlarni <audio> orqali chaladi, shunda DODA
    ovozi telefondа ham chiqadi (brauzer speechSynthesis'дан farqli — haqiqiy uz ovoz).
    Xato bo'lsa b'' qaytaradi."""
    if not text:
        return b""
    lang_voices = VOICES.get(VOICE_GENDER, VOICES["male"])
    voice = lang_voices.get(lang, lang_voices["uz"])
    params = EMOTIONS.get(emotion or CURRENT_EMOTION, EMOTIONS["neutral"])
    path = os.path.join(tempfile.gettempdir(),
                        "doda_tts_" + str(random.randint(0, 10 ** 7)) + ".mp3")
    try:
        asyncio.run(edge_tts.Communicate(text, voice, **params).save(path))
        with open(path, "rb") as f:
            return f.read()
    except Exception as e:
        _report_error("tts_bytes", e)
        return b""
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass


def _cleanup_temp_files():
    """Ishga tushганда oldingi ishдан qolган vaqtinchalik fayllarni tozalaydi
    (audio/ekran/kamera/ovoz). Diskда 'musor' yig'ilmasligini kafolatlaydi."""
    import glob
    tmp = tempfile.gettempdir()
    for pat in ("doda_audio_*.mp3", "doda_tts_*.mp3", "doda_screen_*", "doda_camera_*",
                "doda_*.ogg", "doda_*.wav", "doda_cam_*", "doda_vid_*", ".doda_srtest.png"):
        for f in glob.glob(os.path.join(tmp, pat)):
            try:
                os.remove(f)
            except OSError:
                pass


# ===== Tizim buyruqlari (macOS) =====
# Ilova/sayt/tizim harakatlari. Bular macOS uchun (`open`, `osascript`, `pmset`).

def open_app(app_name, spoken):
    """macOS'da ilovani ochadi. O'rnatilmagan bo'lsa xabar beradi."""
    try:
        result = subprocess.run(["open", "-a", app_name])
    except Exception as e:
        print("open_app xato:", e)
        say("Ilovani ocholmadim.", lang="uz")
        return
    if result.returncode == 0:
        say(spoken, lang="uz")
    else:
        say(app_name + " topilmadi yoki o'rnatilmagan.", lang="uz")


def _open_url(url):
    """URL'ni ochadi. macOS 'open' buyrug'i — launchd (bot) fon jarayonidan ham ishonchli;
    webbrowser.open ba'zan fon jarayonda brauzerni ochmaydi."""
    try:
        r = subprocess.run(["open", url], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return True
    except Exception:
        pass
    try:
        return webbrowser.open(url)
    except Exception:
        return False


def open_website(url, spoken):
    """Brauzerda saytni ochadi."""
    _open_url(url)
    say(spoken, lang="uz")


def open_app_or_web(name):
    """Avval ilova sifatida ochishga urinadi. O'rnatilmagan bo'lsa brauzerdan qidirib ochadi."""
    name = name.strip()
    if not name:
        say("Nimani ochay?", lang="uz")
        return
    # 1) Ilova sifatida ochishga urinamiz (macOS 'open -a')
    try:
        result = subprocess.run(["open", "-a", name], capture_output=True, text=True)
        if result.returncode == 0:
            say(name + " ochilyapti.", lang="uz")
            return
    except Exception:
        pass
    # 2) O'rnatilmagan -> brauzerdan Google orqali qidirib ochamiz
    url = SEARCH_ENGINES.get("google", "https://www.google.com/search?q=") + urllib.parse.quote(name)
    _open_url(url)
    say(name + " ilovasi topilmadi, brauzerdan qidirib ochyapman.", lang="uz")


def open_folder(path, spoken):
    """Finder'da papkani ochadi."""
    subprocess.Popen(["open", os.path.expanduser(path)])
    say(spoken, lang="uz")


def change_volume(direction):
    """Ovoz balandligi: 'up' / 'down' / 'mute'."""
    if direction == "up":
        script = "set volume output volume (output volume of (get volume settings) + 15)"
    elif direction == "down":
        script = "set volume output volume (output volume of (get volume settings) - 15)"
    else:
        script = "set volume with output muted"
    subprocess.run(["osascript", "-e", script])
    say("Bajarildi.", lang="uz")


def take_screenshot():
    """Ekran suratini ish stoliga saqlaydi."""
    path = os.path.join(os.path.expanduser("~/Desktop"),
                        "screenshot_" + str(random.randint(0, 100000)) + ".png")
    subprocess.run(["screencapture", path])
    say("Skrinshot ish stoliga saqlandi.", lang="uz")


def battery_status():
    """Batareya foizini aytadi."""
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"], text=True)
        m = re.search(r"(\d+)%", out)
        pct = m.group(1) if m else "?"
        say("Batareya " + pct + " foiz.", lang="uz")
    except Exception as e:
        print("battery_status xato:", e)
        say("Batareyani aniqlolmadim.", lang="uz")


def system_sleep():
    """Kompyuterni uyqu rejimiga o'tkazadi."""
    say("Uyqu rejimiga o'tyapman.", lang="uz")
    subprocess.run(["pmset", "sleepnow"])


def say_random(options, lang="uz"):
    """Berilgan javoblardan tasodifiy birini aytadi (tabiiyroq bo'lishi uchun)."""
    say(random.choice(options), lang=lang)


# ===== Eslatma tizimi =====
_reminders = []  # [{"time": datetime, "text": str, "fired": bool}]


def _parse_time(text):
    """Matndan vaqtni ajratadi: '10:00', '10 30', 'soat 10', '10 da' -> bugun/ertaga uchun datetime."""
    m = re.search(r"(\d{1,2})[:.\s](\d{2})", text)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
    else:
        m = re.search(r"soat\s*(\d{1,2})", text) or re.search(r"(\d{1,2})\s*da\b", text)
        if m:
            h, mi = int(m.group(1)), 0
        else:
            return None
    if not (0 <= h < 24 and 0 <= mi < 60):
        return None
    now = dt.datetime.now()
    target = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)  # vaqt o'tib ketgan bo'lsa -> ertaga
    return target


def _reminder_note(message):
    """Eslatma matnини (vaqt va buyruq so'zlarisiz) qaytaradi."""
    note = _norm(message)
    note = re.sub(r"\d+\s*(soatdan|soat|daqiqadan|daqiqa|minutdan|minut|soniyadan|soniya|часов|часа|час|минут|секунд)\w*", " ", note)
    note = re.sub(r"soat\s*\d{1,2}([:.\s]\d{2})?", " ", note)
    for w in ("dan keyin", "keyin", "song", "через", "menga", "eslatib qoy", "eslatib ber",
              "eslatib", "eslat", "eslab qol", "budilnik", "alarm", "uygotib", "uygot",
              "tugiz", "tug'iz", "turg'iz", "turgiz", "uyg'otib", "напомни",
              "разбуди", "da ", "doda", "iltimos", "bor"):
        note = note.replace(w, " ")
    note = " ".join(note.split()).strip()
    return note or "eslatma"


def parse_reminder(message):
    """Eslatma vaqtini soniyaда (delay) va matnini qaytaradi. Nisbiy va absolyut.
    -> (delay_seconds, note) yoki (None, None)."""
    m = _norm(message)
    # Nisbiy: "2 soatdan keyin", "5 daqiqadan keyin", "через 10 минут"
    rel = re.search(r"(\d+)\s*(soatdan|soat|daqiqadan|daqiqa|minutdan|minut|soniyadan|soniya|часов|часа|час|минут|секунд)", m)
    if rel and any(w in m for w in ("keyin", "song", "через", "keyn")):
        n = int(rel.group(1))
        u = rel.group(2)
        if u.startswith("soat") or u.startswith("час"):
            delay = n * 3600
        elif u.startswith("son") or u.startswith("секунд"):
            delay = n
        else:
            delay = n * 60
        return max(delay, 1), _reminder_note(message)
    # Absolyut vaqt: "soat 15 da", "10:30"
    target = _parse_time(message)
    if target is not None:
        delay = int((target - dt.datetime.now()).total_seconds())
        return max(delay, 1), _reminder_note(message)
    return None, None


def is_reminder(message):
    """Xabar eslatma/budilnik buyrug'imi?"""
    m = _norm(message)
    # Aniq budilnik/uyg'otish so'zlari — vaqt bo'lmasa ham eslatma
    if any(k in m for k in ("budilnik", "alarm", "uygot", "uyg'ot", "uygotib", "tugiz", "tug'iz",
                            "turg'iz", "turgiz", "uyg'otib", "будильник", "разбуди")):
        return True
    # eslat / eslab qol / napomni — FAQAT vaqt aniqlansa eslatma
    # (aks holda "eslab qol bu Alisher" kabi yuz-xotira buyrug'iga xalaqit bermaydi)
    if any(k in m for k in ("eslat", "eslab qol", "eslatib", "menga eslat", "напомни")) and "eslatma" not in m:
        return parse_reminder(message)[0] is not None
    return False


def add_reminder(message):
    """Eslatma qo'yadi (nisbiy yoki absolyut vaqt bilan). Kompyuterда ovoz bilan eslatadi."""
    delay, note = parse_reminder(message)
    if delay is None:
        say("Kechirasiz, vaqtni tushunmadim. Masalan: 'soat 15 da eslat' yoki '2 soatdan keyin eslat'.", lang="uz")
        return
    target = dt.datetime.now() + dt.timedelta(seconds=delay)
    _reminders.append({"time": target, "text": note, "fired": False})
    say("Yaxshi, soat " + target.strftime("%H:%M") + " da eslataman: " + note + ".", lang="uz")


# ===== Foydalanuvchi ismi (xotira) =====
USER_NAME_FILE = os.path.expanduser("~/.doda_user_name")


def _load_user_name():
    try:
        if os.path.exists(USER_NAME_FILE):
            return open(USER_NAME_FILE).read().strip()
    except Exception:
        pass
    return ""


def _save_user_name(name):
    try:
        with open(USER_NAME_FILE, "w") as f:
            f.write(name)
    except Exception as e:
        print("ism saqlanmadi:", e)


def handle_user_name(message):
    """Foydalanuvchi ismini so'raydi/aytadi/eslab qoladi. Bajarsa True."""
    m = _norm(message)
    # So'rov: "men kimman", "mening ismim nima", "ismimni bilasanmi"
    if any(k in m for k in ("men kimman", "ismimni bilasan", "mening ismim nima",
                            "ismim nima", "kim ekanman", "kim ekanimni", "meni tanidingmi")):
        name = _load_user_name()
        if name:
            say_random(["Siz " + name + " siz!", "Sizning ismingiz " + name + ".",
                        "Albatta, siz " + name + "!"], "uz")
        else:
            say("Kechirasiz, ismingizni hali bilmayman. \"Mening ismim ...\" deb ayting, eslab qolaman.", lang="uz")
        return True
    # O'rnatish: "mening ismim Ali", "ismim Ali", "meni Ali deb chaqir"
    mm = re.search(r"meni\s+([A-Za-zА-Яа-яЁё']+)\s+deb", message, re.IGNORECASE)
    if not mm:
        mm = re.search(r"(?:mening ismim|ismim)\s+([A-Za-zА-Яа-яЁё']+)", message, re.IGNORECASE)
    if mm and _norm(mm.group(1)) not in ("nima", "kim", "deb", "bilasan"):
        name = mm.group(1).strip("'").capitalize()
        _save_user_name(name)
        say_random(["Tanishganimdan xursandman, " + name + "! Ismingizni eslab qoldim.",
                    "Yaxshi, " + name + "! Endi ismingizni bilaman."], "uz")
        return True
    return False


REMINDERS_FILE = os.path.expanduser("~/.doda_reminders.json")


def list_reminders():
    """Faol eslatmalarni ro'yxat qilib aytadi (fayldan + xotiradan)."""
    now = time.time()
    items = []
    try:
        if os.path.exists(REMINDERS_FILE):
            items = [x for x in json.load(open(REMINDERS_FILE)) if x.get("fire", 0) > now]
    except Exception:
        items = []
    # desktop (xotira)dagilar ham
    for r in _reminders:
        if not r["fired"] and r["time"] > dt.datetime.now():
            items.append({"fire": r["time"].timestamp(), "note": r["text"]})
    parts = []
    for x in sorted(items, key=lambda z: z.get("fire", 0)):
        tstr = dt.datetime.fromtimestamp(x["fire"]).strftime("%H:%M")
        parts.append(x.get("note", "") + " — soat " + tstr)
    # takroriy eslatmalar
    for it in _load_recurring():
        parts.append(it.get("note", "") + " — " + _days_name(it.get("days", [])) +
                     " soat " + ("%02d:%02d" % (it["hh"], it["mm"])))
    if not parts:
        say("Faol eslatma yo'q.", lang="uz")
        return
    say("Faol eslatmalar: " + "; ".join(parts) + ".", lang="uz")


def cancel_reminders():
    """Barcha faol eslatma/budilniklarni bekor qiladi (bir martalik + takroriy)."""
    n = sum(1 for r in _reminders if not r["fired"])
    for r in _reminders:
        r["fired"] = True
    for f in (REMINDERS_FILE, RECURRING_FILE):
        try:
            if os.path.exists(f):
                n += len(json.load(open(f)))
                os.remove(f)
        except Exception:
            pass
    say("Barcha eslatmalar bekor qilindi." if n else "Faol eslatma yo'q.", lang="uz")


# ===== Takroriy eslatmalar (har kuni / ish kunlari / muayyan kunlar) =====
RECURRING_FILE = os.path.expanduser("~/.doda_recurring.json")
_WEEKDAYS_UZ = {"dushanba": 0, "seshanba": 1, "chorshanba": 2, "payshanba": 3,
                "juma": 4, "shanba": 5, "yakshanba": 6}
_KUN_NOMLARI = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]


def _load_recurring():
    try:
        return json.load(open(RECURRING_FILE)) if os.path.exists(RECURRING_FILE) else []
    except Exception:
        return []


def _save_recurring(items):
    try:
        with open(RECURRING_FILE, "w") as f:
            json.dump(items, f)
    except Exception:
        pass


def _parse_hhmm(text):
    mm = re.search(r"(\d{1,2})[:.\s](\d{2})", text)
    if mm:
        return int(mm.group(1)), int(mm.group(2))
    m2 = re.search(r"soat\s*(\d{1,2})", text) or re.search(r"(\d{1,2})\s*da\b", text)
    if m2:
        return int(m2.group(1)), 0
    return None, None


def _parse_days(m):
    if any(w in m for w in ("har kuni", "har kun", "kunda", "har doim")):
        return [0, 1, 2, 3, 4, 5, 6]
    # dam olish (hafta oxiri) ni ish kunlaridan OLDIN tekshiramiz ("olish kun" chalkashmasin)
    if any(w in m for w in ("dam olish", "hafta oxiri")) or ("yakshanba" in m):
        return [5, 6]
    if any(w in m for w in ("ish kun", "budni", "dushanbadan jumagacha")) or ("dushanba" in m and "juma" in m):
        return [0, 1, 2, 3, 4]
    # butun so'z sifatida ("shanba" "dushanba" ichida bo'lmasin)
    days = [v for name, v in _WEEKDAYS_UZ.items() if re.search(r"\b" + name + r"\b", m)]
    return sorted(set(days)) if days else None


def _days_name(days):
    ds = sorted(days)
    if ds == [0, 1, 2, 3, 4, 5, 6]:
        return "har kuni"
    if ds == [0, 1, 2, 3, 4]:
        return "ish kunlari"
    if ds == [5, 6]:
        return "dam olish kunlari"
    return "har " + ", ".join(_KUN_NOMLARI[d] for d in ds)


def is_recurring(message):
    m = _norm(message)
    has_word = any(w in m for w in ("har kuni", "har kun", "kunda", "ish kun", "dushanbadan",
                                    "dam olish", "hafta oxiri", "har dushanba", "har seshanba",
                                    "har chorshanba", "har payshanba", "har juma", "har shanba",
                                    "har yakshanba")) or ("dushanba" in m and "juma" in m)
    return has_word and _parse_hhmm(message)[0] is not None


def parse_recurring(message):
    hh, mm = _parse_hhmm(message)
    if hh is None:
        return None
    days = _parse_days(_norm(message))
    if not days:
        return None
    note = _reminder_note(message)
    # kun nomlarini matndan olib tashlaymiz
    for name in list(_WEEKDAYS_UZ) + ["har kuni", "ish kunlari", "ish kuni", "dam olish", "hafta oxiri", "har", "gacha", "dan"]:
        note = note.replace(name, " ")
    note = " ".join(note.split()).strip() or "eslatma"
    return days, hh, mm, note


def add_recurring(chat_id, days, hh, mm, note):
    items = _load_recurring()
    items.append({"chat_id": chat_id, "days": days, "hh": hh, "mm": mm, "note": note, "last": ""})
    _save_recurring(items)


def pop_due_recurring(now, is_mine):
    """Hozir kelgan takroriy eslatmalarni qaytaradi va 'last'ni bugunga qo'yadi."""
    items = _load_recurring()
    today = now.strftime("%Y-%m-%d")
    hhmm = now.strftime("%H:%M")
    due, changed = [], False
    for it in items:
        if not is_mine(it.get("chat_id")):
            continue
        if it.get("last") == today:
            continue
        if now.weekday() in it.get("days", []) and ("%02d:%02d" % (it["hh"], it["mm"])) == hhmm:
            it["last"] = today
            changed = True
            due.append(it)
    if changed:
        _save_recurring(items)
    return due


def _reminder_loop():
    """Fon rejimida bir martalik VA takroriy eslatmalarni kuzatadi."""
    while True:
        now = dt.datetime.now()
        for r in _reminders:
            if not r["fired"] and r["time"] <= now:
                r["fired"] = True
                say("Eslatma vaqti bo'ldi!", lang="uz")
                say(r["text"], lang="uz")
        for it in pop_due_recurring(now, lambda c: c == "local"):
            say("Eslatma!", lang="uz")
            say(it["note"], lang="uz")
        time.sleep(20)


# ===== Telegram bot uchun bir martalik parol (OTP) =====
# Parol faylga yoziladi, chunki bot alohida jarayonda ishlaydi (telegram_bot.py).
OTP_FILE = os.path.expanduser("~/.doda_otp")


def generate_bot_password():
    """6 xonali tasodifiy bir martalik parol hosil qiladi, faylga yozadi va aytadi."""
    code = "".join(random.choice("0123456789") for _ in range(6))
    try:
        with open(OTP_FILE, "w") as f:
            f.write(code)
        os.chmod(OTP_FILE, 0o600)
    except Exception as e:
        print("OTP faylga yozib bo'lmadi:", e)
    say("Botga kirish paroli: " + "".join(code) + ". Bu parol bir martalik.", lang="uz")


def process_text(message):
    """Buyruqni bajaradi va DODA javob matnini qaytaradi (ovozsiz). Telegram bot ishlatadi."""
    global _capture
    _capture = []
    try:
        handle_massage(message)
    except SystemExit:
        _capture.append("Xayr!")
    except Exception as e:
        _capture.append("Xatolik: " + str(e))
    result = " ".join(_capture).strip()
    _capture = None
    return result or "Bajarildi."


# ===== Suhbat javoblari — javoblar.py faylidan yuklanadi =====
# asistent.py da buyruq YO'Q: harakatlar -> buyruq_baza.py, suhbat javoblari -> javoblar.py
try:
    from javoblar import JAVOBLAR
except Exception as _e:
    print("javoblar.py yuklanmadi:", _e)
    JAVOBLAR = []


def _make_reply(responses, lang):
    """Yopilish (closure) muammosisiz javob funksiyasini yaratadi."""
    return lambda: say_random(responses, lang)


# RULES faqat javoblar.py dagi suhbat javoblaridan iborat.
RULES = [(_kw, _make_reply(_resp, _lang)) for _kw, _resp, _lang in JAVOBLAR]


_claude_client = None       # birinchi suhbatda yuklanadi (lazy-load)
_chat_history = []          # ko'p bosqichli suhbat konteksti: [{"role", "content"}]


def _load_api_key():
    """API kalitini xavfsiz oladi: avval ANTHROPIC_API_KEY env, keyin CLAUDE_KEY_FILE fayli.
    Kalit hech qachon kodda saqlanmaydi. Topilmasa None."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key and key.strip():
        return key.strip()
    p = os.path.expanduser(CLAUDE_KEY_FILE)
    if os.path.exists(p):
        try:
            k = open(p).read().strip()
            return k or None
        except Exception:
            return None
    return None


def _get_claude():
    """Anthropic klientini bir marta yaratadi. Kalit env yoki maxfiy fayldan olinadi."""
    global _claude_client
    if _claude_client is None:
        from anthropic import Anthropic
        key = _load_api_key()
        # Kalit topilsa aniq beramiz; aks holda Anthropic() o'zi env'dan qidiradi
        _claude_client = Anthropic(api_key=key) if key else Anthropic()
    return _claude_client


def chat_with_claude(user_text):
    """Claude bilan erkin suhbat. (javob_matni, til) qaytaradi."""
    client = _get_claude()
    _chat_history.append({"role": "user", "content": user_text})

    # Tuzilgan javob (matn + til) — barcha modellar qo'llab-quvvatlaydi (Haiku 4.5 ham).
    _fmt = {
        "type": "json_schema",
        "schema": {
            "type": "object",
            "properties": {
                "reply": {"type": "string"},
                "lang": {"type": "string", "enum": ["uz", "ru", "en"]},
            },
            "required": ["reply", "lang"],
            "additionalProperties": False,
        },
    }
    kwargs = {
        "model": CHAT_MODEL,
        "max_tokens": CHAT_MAX_TOKENS,
        "system": CHAT_SYSTEM_PROMPT,
        "messages": _chat_history,
    }
    # thinking:disabled va effort FAQAT yangi modellarda (Opus 5 / Sonnet 5 / Opus 4.7+).
    # Haiku 4.5 / Sonnet 4.5 bularni qabul qilmaydi (400 xato) -> ularsiz yuboramiz.
    if "haiku" in CHAT_MODEL.lower() or "sonnet-4-5" in CHAT_MODEL.lower():
        kwargs["output_config"] = {"format": _fmt}
    else:
        kwargs["thinking"] = {"type": "disabled"}   # ovoz uchun tez javob (o'ylashsiz)
        kwargs["output_config"] = {"effort": "low", "format": _fmt}

    response = client.messages.create(**kwargs)

    text = next((b.text for b in response.content if b.type == "text"), "")
    data = json.loads(text)
    reply, lang = data["reply"], data["lang"]
    # Qat'iy himoya: ovoz DOIM o'zbekcha (yoki rus) — ingliz/boshqa til -> o'zbek ovozi.
    if lang not in ("uz", "ru"):
        lang = "uz"

    _chat_history.append({"role": "assistant", "content": text})
    # Tarixni cheklab turamiz (kontekst o'smasligi uchun)
    if len(_chat_history) > CHAT_HISTORY_LIMIT:
        del _chat_history[:-CHAT_HISTORY_LIMIT]

    return reply, lang


def _guess_lang(text):
    """Matn tilini oddiy taxmin qiladi (kirill -> ru, aks holda uz)."""
    return "ru" if re.search(r"[а-яА-ЯёЁ]", text or "") else "uz"


def agent_with_claude(user_text):
    """Claude'ni asboblar (fayl/terminal) bilan ishga soladi — kod agenti rejimi.

    tool_runner aylanani avtomatik boshqaradi: Claude asbob chaqiradi ->
    asbob bajariladi -> natija Claude'ga qaytadi -> Claude tugatguncha davom etadi.
    (javob_matni, til) qaytaradi.
    """
    import agent_tools as agent_tools
    agent_tools.set_workspace(AGENT_WORKSPACE)
    client = _get_claude()

    runner = client.beta.messages.tool_runner(
        model=AGENT_MODEL,
        max_tokens=AGENT_MAX_TOKENS,
        system=AGENT_SYSTEM_PROMPT,
        tools=agent_tools.AGENT_TOOLS,
        messages=[{"role": "user", "content": user_text}],
    )

    final_text = ""
    steps = 0
    for message in runner:
        steps += 1
        # Har bir bosqichdagi matn bloklarini yig'amiz (oxirgisi yakuniy javob bo'ladi)
        texts = [b.text for b in message.content if getattr(b, "type", "") == "text"]
        if texts:
            final_text = " ".join(texts).strip()
        # Qaysi asbob ishlatilganini konsolga chiqaramiz (kuzatish uchun)
        for b in message.content:
            if getattr(b, "type", "") == "tool_use":
                print(f"  [agent] {b.name}({b.input})")
        if steps >= AGENT_MAX_STEPS:
            print("  [agent] maksimal qadamga yetdi, to'xtatildi")
            break

    if not final_text:
        final_text = "Vazifa bajarildi."
    return final_text, _guess_lang(final_text)


def _norm(s):
    """Kichik harf + apostroflarni olib tashlaydi (STT 'zo'r'/'zor' farqini yo'qotadi)."""
    s = s.lower()
    for ch in ("'", "ʻ", "’", "‘", "`"):
        s = s.replace(ch, "")
    return s


# ===== Niyat (intent) tizimi — ma'lumotlar buyruq_baza.py da =====
DEV_PROJECT_DIR = "~"       # Developer buyruqlar (git/flutter/npm...) shu papkada bajariladi. O'zgartiring.
WEATHER_CITY = "Tashkent"   # Standart shahar (ob-havo uchun). "ob havo <shahar>" deb boshqa shahar so'rasa bo'ladi.

_KUNLAR = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
_OYLAR = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
          "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr"]


def _wifi_device():
    """macOS'da Wi-Fi qurilma nomini topadi (odatda en0)."""
    try:
        out = subprocess.check_output(["networksetup", "-listallhardwareports"], text=True)
    except Exception:
        return "en0"
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if "Wi-Fi" in ln or "AirPort" in ln:
            for j in range(i, min(i + 3, len(lines))):
                mm = re.search(r"Device:\s*(\w+)", lines[j])
                if mm:
                    return mm.group(1)
    return "en0"


def media_control(action):
    """Media boshqaruvi (Apple Music ilovasi orqali)."""
    scripts = {
        "play": 'tell application "Music" to playpause',
        "pause": 'tell application "Music" to playpause',
        "stop": 'tell application "Music" to stop',
        "next": 'tell application "Music" to next track',
        "previous": 'tell application "Music" to previous track',
    }
    if action in scripts:
        subprocess.run(["osascript", "-e", scripts[action]])
        say("Bajarildi.", lang="uz")
    elif action == "fullscreen":
        subprocess.run(["osascript", "-e",
                        'tell application "System Events" to key code 3 using {command down, control down}'])
        say("To'liq ekran.", lang="uz")
    elif action == "shuffle":
        subprocess.run(["osascript", "-e",
                        'tell application "Music" to set shuffle enabled to not (shuffle enabled)'])
        say("Aralashtirish o'zgartirildi.", lang="uz")
    elif action == "repeat":
        subprocess.run(["osascript", "-e", 'tell application "Music" to set song repeat to one'])
        say("Takrorlash yoqildi.", lang="uz")


def system_control(action):
    """Tizim boshqaruvi: qulflash, uyqu, wifi, ovoz, holat va h.k."""
    if action == "lock":
        subprocess.run(["pmset", "displaysleepnow"])
        say("Ekran qulflandi.", lang="uz")
    elif action == "sleep":
        say("Uxlayapman.", lang="uz")
        subprocess.run(["pmset", "sleepnow"])
    elif action == "restart":
        say("Qayta ishga tushiryapman.", lang="uz")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to restart'])
    elif action == "shutdown":
        say("Kompyuterni o'chiryapman.", lang="uz")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to shut down'])
    elif action in ("wifi_on", "wifi_off"):
        subprocess.run(["networksetup", "-setairportpower", _wifi_device(),
                        "on" if action == "wifi_on" else "off"])
        say("Vayfay " + ("yoqildi." if action == "wifi_on" else "o'chirildi."), lang="uz")
    elif action in ("bt_on", "bt_off"):
        if subprocess.run(["which", "blueutil"], capture_output=True).returncode == 0:
            subprocess.run(["blueutil", "--power", "1" if action == "bt_on" else "0"])
            say("Bluetooth " + ("yoqildi." if action == "bt_on" else "o'chirildi."), lang="uz")
        else:
            say("Bluetooth uchun blueutil kerak. Terminalda 'brew install blueutil' deb o'rnating.", lang="uz")
    elif action in ("bright_up", "bright_down"):
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code '
                        + ("144" if action == "bright_up" else "145")])
        say("Bajarildi.", lang="uz")
    elif action == "mute":
        change_volume("mute")
    elif action == "unmute":
        subprocess.run(["osascript", "-e", "set volume without output muted"])
        say("Ovoz qaytarildi.", lang="uz")
    elif action == "vol_up":
        change_volume("up")
    elif action == "vol_down":
        change_volume("down")
    elif action == "screenshot":
        take_screenshot()
    elif action == "battery":
        battery_status()
    elif action == "cpu":
        try:
            vals = subprocess.check_output(["ps", "-A", "-o", "%cpu"], text=True).split()[1:]
            total = sum(float(x) for x in vals if x.replace(".", "", 1).isdigit())
            say("Protsessor yuklanishi taxminan " + str(int(total)) + " foiz.", lang="uz")
        except Exception:
            say("Aniqlolmadim.", lang="uz")
    elif action == "memory":
        try:
            vals = subprocess.check_output(["ps", "-A", "-o", "%mem"], text=True).split()[1:]
            total = sum(float(x) for x in vals if x.replace(".", "", 1).isdigit())
            say("Xotira ishlatilishi taxminan " + str(int(total)) + " foiz.", lang="uz")
        except Exception:
            say("Aniqlolmadim.", lang="uz")
    elif action == "internet":
        say("Internet ishlayapti." if _has_internet() else "Internet yo'q.", lang="uz")
    elif action == "emptytrash":
        subprocess.run(["osascript", "-e", 'tell application "Finder" to empty trash'])
        say("Savatcha bo'shatildi.", lang="uz")


def time_info(key):
    """Vaqt / sana / kun / oy / yil / hafta."""
    now = dt.datetime.now()
    if key == "time":
        say("Hozir soat " + now.strftime("%H:%M") + ".", lang="uz")
    elif key == "date":
        say("Bugun " + str(now.day) + "-" + _OYLAR[now.month - 1] + ", " + str(now.year) + "-yil.", lang="uz")
    elif key == "day":
        say("Bugun " + _KUNLAR[now.weekday()] + ".", lang="uz")
    elif key == "month":
        say("Hozir " + _OYLAR[now.month - 1] + " oyi.", lang="uz")
    elif key == "year":
        say(str(now.year) + "-yil.", lang="uz")
    elif key == "week":
        say("Yilning " + str(now.isocalendar()[1]) + "-haftasi.", lang="uz")


def run_dev(cmd):
    """Developer buyrug'ini Terminalda (DEV_PROJECT_DIR papkasida) bajaradi."""
    d = os.path.expanduser(DEV_PROJECT_DIR)
    script = 'tell application "Terminal" to do script "cd ' + d + ' && ' + cmd + '"'
    subprocess.run(["osascript", "-e", script])
    say("Terminalda bajaryapman.", lang="uz")


def start_timer(message):
    """Matndan raqamni olib, timer (fon rejimida) qo'yadi."""
    m = _norm(message)
    num = re.search(r"(\d+)", m)
    if not num:
        say("Necha daqiqaga timer qo'yay?", lang="uz")
        return
    val = int(num.group(1))
    if "sekund" in m or "soniya" in m or "секунд" in m:
        secs, unit = val, "soniya"
    else:
        secs, unit = val * 60, "daqiqa"
    say(str(val) + " " + unit + "lik timer qo'yildi.", lang="uz")
    threading.Timer(secs, lambda: say("Timer tugadi!", lang="uz")).start()


def make_call(message):
    """FaceTime orqali qo'ng'iroq. 'video' bo'lsa video, aks holda audio.
    Raqam, email yoki kontakt ismini gapdan ajratadi."""
    m = _norm(message)
    video = "video" in m
    email = re.search(r"\S+@\S+", message)
    num = re.search(r"[\+\d][\d\s\-]{4,}", message)
    if email:
        target = email.group(0)
    elif num:
        target = re.sub(r"[\s\-]", "", num.group(0))
    else:
        # ism: qo'ng'iroq fe'llarini olib tashlab qolgan matn
        t = m
        for w in ("qongiroq qil", "qongiroq", "telefon qil", "telefon", "позвони",
                  "call", "facetime", "feystaym", "videochat", "video chat",
                  "video", "chat", "ochib ber", "ochib", "och", "ber", "qil",
                  "ni", "ga", "kir", "doda", "iltimos"):
            t = t.replace(w, " ")
        target = " ".join(t.split()).strip()
    if not target:
        subprocess.run(["open", "-a", "FaceTime"])
        say("Kimga qo'ng'iroq qilay? Raqam yoki ismni ayting.", lang="uz")
        return
    scheme = "facetime://" if video else "facetime-audio://"
    subprocess.run(["open", scheme + urllib.parse.quote(target)])
    say(target + " ga " + ("video " if video else "") + "qo'ng'iroq qilyapman.", lang="uz")


def _send_imessage(recipient, text):
    """Messages (iMessage/SMS) orqali xabar yuboradi."""
    if re.search(r"\d", recipient):
        recipient = re.sub(r"[\s\-]", "", recipient)
    safe_text = text.replace("\\", "\\\\").replace('"', '\\"')
    safe_to = recipient.replace('"', '\\"')
    script = ('tell application "Messages"\n'
              '  set svc to 1st service whose service type = iMessage\n'
              '  send "%s" to buddy "%s" of svc\n'
              'end tell') % (safe_text, safe_to)
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode == 0:
        say(recipient + " ga xabar yuborildi.", lang="uz")
    else:
        say("Xabarni yuborolmadim. Messages ilovasi sozlanganini tekshiring.", lang="uz")


def send_sms(message):
    """SMS/iMessage yuboradi. 'sms yoz X ga matn' (bir zumda) yoki bosqichma-bosqich."""
    body = message.strip()
    low = body.lower()
    for p in ("sms yozib yubor", "sms yoz", "sms yubor", "sms jonat", "xabar yozib yubor",
              "xabar yoz", "xabar yubor", "смс напиши", "смс отправь", "message", "смс", "sms"):
        idx = low.find(p)
        if idx != -1:
            body = body[idx + len(p):].strip()
            break
    m = re.match(r"(.+?)\s*ga\s+(.+)$", body, re.IGNORECASE | re.DOTALL)
    if m:
        _send_imessage(m.group(1).strip(), m.group(2).strip())
        return
    # Ma'lumot to'liq emas
    if _capture is not None:  # bot rejimi -> interaktiv emas
        say("Format: 'sms yoz raqam ga xabar' deb yuboring.", lang="uz")
        return
    # Desktop: bosqichma-bosqich so'raymiz
    say("Kimga yozay? Raqam yoki ismni ayting.", lang="uz")
    recipient = listen()
    if not str(recipient).strip():
        say("Tushunmadim.", lang="uz")
        return
    say("Nima yozay?", lang="uz")
    text = listen()
    if not str(text).strip():
        say("Tushunmadim.", lang="uz")
        return
    _send_imessage(str(recipient).strip(), str(text).strip())


TELEGRAM_APP = "Telegram"   # Telegram Desktop ilova nomi (yoki "Telegram Lite")


def _send_telegram_ui(recipient, text, do_send=True):
    """Telegram Desktop'ni avtomatlashtirib kontaktga xabar yuboradi (Accessibility kerak).
    Qidiruv -> birinchi natijani ochish -> matnni qo'yish -> (do_send bo'lsa) yuborish.
    do_send=False bo'lsa matnni yozadi-yu, YUBORMAYDI (sinov uchun xavfsiz)."""
    # Unicode uchun ishonchli: nom va matnni clipboard orqali qo'yamiz
    def _paste(s):
        subprocess.run(["pbcopy"], input=(s or "").encode("utf-8"))
        subprocess.run(["osascript", "-e",
                        'tell application "System Events" to keystroke "v" using {command down}'],
                       capture_output=True)
    try:
        subprocess.run(["open", "-a", TELEGRAM_APP], capture_output=True)
        time.sleep(1.2)
        SE = 'tell application "System Events" to '
        # Ochiq Mini App / dialog / chatni yopamiz (Escape) — aks holda bosishlar
        # ochiq oynaga ketib qoladi (mo'rtlikni kamaytiradi)
        for _ in range(2):
            subprocess.run(["osascript", "-e", SE + 'key code 53'], capture_output=True)  # Esc
            time.sleep(0.25)
        # Global qidiruvni ochamiz (tdesktop macOS: Cmd+K)
        subprocess.run(["osascript", "-e", SE + 'keystroke "k" using {command down}'],
                       capture_output=True)
        time.sleep(0.6)
        # Eski matnni tozalab, kontakt nomini qo'yamiz
        subprocess.run(["osascript", "-e", SE + 'keystroke "a" using {command down}'],
                       capture_output=True)
        _paste(recipient)
        time.sleep(1.0)                                   # natijalar yuklanishini kutamiz
        # Birinchi natijani tanlaymiz: pastga strelka + Enter
        subprocess.run(["osascript", "-e", SE + 'key code 125'], capture_output=True)  # ↓
        time.sleep(0.3)
        subprocess.run(["osascript", "-e", SE + 'key code 36'], capture_output=True)   # Enter -> chatni ochadi
        time.sleep(0.8)
        # Xabar matnini yozamiz (chat ochilganda kiritish maydoni fokusda bo'ladi)
        _paste(text)
        time.sleep(0.4)
        if do_send:
            subprocess.run(["osascript", "-e", SE + 'key code 36'], capture_output=True)  # Enter -> yuboradi
            return True
        return True
    except Exception as e:
        _report_error("telegram yuborish", e)
        return False


def parse_telegram_send(message):
    """«telegramda Onamga salom yubor» -> ('Onam', 'salom'). Topilmasa (None, None).
    Grammatika: [telegram...] <kim> ga <matn> [yubor/jonat/yoz]."""
    body = message.strip()
    low = body.lower()
    # "telegram", "telegramda", "telegramga kirib", "telegram orqali" prefikslarini olib tashlaymiz
    for p in ("telegramga kirib", "telegram orqali", "telegramdan", "telegramda", "telegramga",
              "telegram"):
        idx = low.find(p)
        if idx != -1:
            body = (body[:idx] + body[idx + len(p):]).strip()
            low = body.lower()
            break
    # oxiridagi yuborish fe'llarini olib tashlaymiz
    for suf in ("degan xabar yubor", "degan xabarni yubor", "deb yubor", "deb yozib yubor",
                "yozib yubor", "jonat", "jo'nat", "yubor", "yoz"):
        if low.endswith(suf):
            body = body[: len(body) - len(suf)].strip()
            low = body.lower()
            break
    m = re.match(r"(.+?)\s*ga\s+(.+)$", body, re.IGNORECASE | re.DOTALL)
    if not m:
        return None, None
    recipient, text = m.group(1).strip(), m.group(2).strip()
    # "degan"/"deb" qoldiqlarini tozalaymiz (masalan: «salom degan»)
    text = re.sub(r"\s+(deg[ao]n|deb)$", "", text).strip().strip('"“”')
    return recipient, text


def _telegram_confirm_send():
    """Tayyor turgan (chat ochiq, matn kiritish maydonida) xabarni Enter bilan YUBORADI."""
    try:
        subprocess.run(["open", "-a", TELEGRAM_APP], capture_output=True)
        time.sleep(0.6)
        subprocess.run(["osascript", "-e",
                        'tell application "System Events" to key code 36'],  # Enter
                       capture_output=True)
        return True
    except Exception as e:
        _report_error("telegram tasdiqlab yuborish", e)
        return False


def _telegram_cancel_send():
    """Bekor: kiritish maydonidagi tayyor matnni tozalaydi (Cmd+A -> Delete) — yuborilmaydi."""
    try:
        subprocess.run(["open", "-a", TELEGRAM_APP], capture_output=True)
        time.sleep(0.5)
        SE = 'tell application "System Events" to '
        subprocess.run(["osascript", "-e", SE + 'keystroke "a" using {command down}'],
                       capture_output=True)
        time.sleep(0.15)
        subprocess.run(["osascript", "-e", SE + 'key code 51'], capture_output=True)  # Delete
        return True
    except Exception as e:
        _report_error("telegram bekor qilish", e)
        return False


def send_telegram(message):
    """Telegram orqali kontaktga xabar. Masalan: «telegramda Onamga salom yubor».
    Grammatika: [telegram...] <kim> ga <matn> [yubor/jonat/yoz].
    DESKTOP (ovoz) rejimi: chatni ochib, matnни ko'rsatib, YUBORISHDAN OLDIN ovozli
    tasdiq so'raydi (noto'g'ri kontaktга ketmaslik uchun). Bot rejimida tasdiqlash
    skrinshot+tugma bilan telegram_bot.py da amalga oshadi (bu funksiya chaqirilmaydi)."""
    recipient, text = parse_telegram_send(message)
    if recipient:
        if _capture is not None:
            # bot rejimi bu yerga kelmasligi kerak (bot o'zi ushlaydi), lekin xavfsizlik uchun:
            say("Telegram yuborish botда tugma orqali tasdiqlanadi.", lang="uz")
            return
        # DESKTOP: chatni tayyorlaymiz (YUBORMASDAN), so'ng ovozli tasdiq
        say("Telegramда «%s» ga «%s» tayyorladim. Yuboraymi? «Ha» yoki «yo'q» deng." % (recipient, text), lang="uz")
        if not _send_telegram_ui(recipient, text, do_send=False):
            say("Telegramда tayyorlolmadim. Ilova ochiqmi va ruxsat bormi tekshiring.", lang="uz")
            return
        answer = _norm(str(listen() or ""))
        if any(w in answer for w in ("ha", "xa", "yubor", "mayli", "bo'ladi", "boladi", "da", "yes")):
            if _telegram_confirm_send():
                say("Yuborildi.", lang="uz")
            else:
                say("Yuborolmadim.", lang="uz")
        else:
            _telegram_cancel_send()
            say("Bekor qildim, yubormadim.", lang="uz")
        return
    # Format to'liq emas
    if _capture is not None:      # bot rejimi
        say("Format: «telegramda <kim> ga <matn> yubor» deb yuboring.", lang="uz")
        return
    say("Kimga yozay?", lang="uz")
    recipient = listen()
    if not str(recipient).strip():
        say("Tushunmadim.", lang="uz"); return
    say("Nima yozay?", lang="uz")
    text = listen()
    if not str(text).strip():
        say("Tushunmadim.", lang="uz"); return
    if _send_telegram_ui(str(recipient).strip(), str(text).strip()):
        say("Yuborildi.", lang="uz")


_stopwatch_start = None


def handle_stopwatch(action):
    """Sekundomer: 'start' boshlaydi, 'stop' o'tgan vaqtni aytadi."""
    global _stopwatch_start
    if action == "start":
        _stopwatch_start = time.time()
        say("Sekundomer boshlandi.", lang="uz")
    else:
        if _stopwatch_start is None:
            say("Sekundomer hali ishga tushmagan.", lang="uz")
            return
        elapsed = int(time.time() - _stopwatch_start)
        _stopwatch_start = None
        say(str(elapsed) + " soniya o'tdi.", lang="uz")


def get_weather(message):
    """wttr.in (bepul, kalitsiz) orqali ob-havoni aytadi. 'ertaga' bo'lsa — bashorat."""
    m = _norm(message)
    ertaga = "ertaga" in m or "завтра" in m
    city = WEATHER_CITY
    mm = re.search(r"(?:ob havo|obhavo|погода|havo)\s+([a-zа-яё]{3,})", m)
    if mm and mm.group(1) not in ("qanday", "qanaqa", "bugun", "hozir", "ertaga", "сегодня", "сейчас", "завтра"):
        city = mm.group(1)
    if ertaga:
        try:
            url = "https://wttr.in/" + urllib.parse.quote(city) + "?format=j1&lang=ru"
            req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=8) as r:
                d = json.loads(r.read().decode("utf-8"))
            tom = d["weather"][1]
            mn, mx = tom["mintempC"], tom["maxtempC"]
            hourly = tom["hourly"][4]
            cond = (hourly.get("lang_ru", [{}])[0].get("value")
                    or hourly["weatherDesc"][0]["value"])
            say(city + " da ertaga " + mn + " dan " + mx + " gradusgacha, " + cond + ".", lang="uz")
        except Exception as e:
            print("weather(ertaga) xato:", e)
            say("Ertangi ob-havoni ololmadim.", lang="uz")
        return
    try:
        url = "https://wttr.in/" + urllib.parse.quote(city) + "?format=%C|%t&lang=ru&m"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=7) as r:
            data = r.read().decode("utf-8").strip()
        parts = data.split("|")
        cond = parts[0].strip() if parts else ""
        temp = parts[1].strip() if len(parts) > 1 else ""
        say(city + " da hozir " + temp + ", " + cond + ".", lang="uz")
    except Exception as e:
        print("weather xato:", e)
        say("Ob-havo ma'lumotini ololmadim. Internet borligini tekshiring.", lang="uz")


_CRYPTO = {"bitcoin": "bitcoin", "bitkoin": "bitcoin", "btc": "bitcoin", "биткоин": "bitcoin",
           "efirium": "ethereum", "ethereum": "ethereum", "efir": "ethereum", "eth": "ethereum",
           "dogecoin": "dogecoin", "doge": "dogecoin", "tether": "tether", "usdt": "tether",
           "bnb": "binancecoin", "solana": "solana", "sol": "solana", "ripple": "ripple", "xrp": "ripple"}
_CRYPTO_NAME = {"bitcoin": "Bitcoin", "ethereum": "Efirium", "dogecoin": "Dogecoin",
                "tether": "Tether", "binancecoin": "BNB", "solana": "Solana", "ripple": "Ripple"}


def get_crypto(message):
    """Kripto valyuta narxini aytadi (bepul CoinGecko API)."""
    m = _norm(message)
    coin = "bitcoin"
    for k, v in _CRYPTO.items():
        if k in m:
            coin = v
            break
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=" + coin + "&vs_currencies=usd"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            price = json.loads(r.read().decode("utf-8"))[coin]["usd"]
        ptxt = format(int(price), ",").replace(",", " ") if price >= 100 else str(round(price, 4))
        say(_CRYPTO_NAME.get(coin, coin) + " narxi taxminan " + ptxt + " dollar.", lang="uz")
    except Exception as e:
        print("crypto xato:", e)
        say("Kripto narxini ololmadim. Internet borligini tekshiring.", lang="uz")


_HIJRIY_OYLAR = ["Muharram", "Safar", "Rabiul-avval", "Rabiul-oxir", "Jumadul-avval",
                 "Jumadul-oxir", "Rajab", "Sha'bon", "Ramazon", "Shavvol", "Zulqa'da", "Zulhijja"]


def get_hijri_date(message):
    """Bugungi hijriy (islomiy) sanani aytadi (bepul Aladhan API)."""
    try:
        today = dt.datetime.now().strftime("%d-%m-%Y")
        with urllib.request.urlopen("http://api.aladhan.com/v1/gToH?date=" + today, timeout=8) as r:
            h = json.loads(r.read().decode("utf-8"))["data"]["hijri"]
        oy = _HIJRIY_OYLAR[int(h["month"]["number"]) - 1]
        say("Bugun hijriy " + h["day"] + " " + oy + " " + h["year"] + " yil.", lang="uz")
    except Exception as e:
        print("hijri xato:", e)
        say("Hijriy sanani ololmadim.", lang="uz")


def get_prayer_times(message):
    """Namoz vaqtlarini aytadi (bepul Aladhan API). Muayyan namoz so'ralsa — o'shani."""
    m = _norm(message)
    try:
        url = ("http://api.aladhan.com/v1/timingsByCity?city=" + urllib.parse.quote(WEATHER_CITY)
               + "&country=Uzbekistan&method=14")
        with urllib.request.urlopen(url, timeout=8) as r:
            t = json.loads(r.read().decode("utf-8"))["data"]["timings"]
        pairs = [("bomdod", "Fajr"), ("peshin", "Dhuhr"), ("asr", "Asr"),
                 ("shom", "Maghrib"), ("xufton", "Isha")]
        for uz, key in pairs:
            if uz in m:
                say(uz.capitalize() + " namozi soat " + t[key] + " da.", lang="uz")
                return
        parts = [uz.capitalize() + " " + t[key] for uz, key in pairs]
        say(WEATHER_CITY + " uchun bugungi namoz vaqtlari: " + ", ".join(parts) + ".", lang="uz")
    except Exception as e:
        print("prayer xato:", e)
        say("Namoz vaqtlarini ololmadim. Internet borligini tekshiring.", lang="uz")


def get_news(message):
    """Google News (bepul RSS) dan asosiy o'zbekcha yangiliklarni aytadi."""
    try:
        import xml.etree.ElementTree as ET
        url = "https://kun.uz/uz/news/rss"   # o'zbekcha (lotin) yangiliklar
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            root = ET.fromstring(r.read().decode("utf-8"))
        titles = []
        for item in root.iter("item"):
            t = item.findtext("title")
            if t:
                titles.append(t.split(" - ")[0].strip())  # manba nomini olib tashlaymiz
            if len(titles) >= 4:
                break
        if not titles:
            say("Yangiliklarni ololmadim.", lang="uz")
            return
        say("Asosiy yangiliklar: " + ". ".join(titles) + ".", lang="uz")
    except Exception as e:
        print("news xato:", e)
        say("Yangiliklarni ololmadim. Internet borligini tekshiring.", lang="uz")


def get_wiki(message):
    """Wikipedia (bepul API) dan mavzu bo'yicha qisqa ma'lumot aytadi."""
    # Mavzuni ORIGINAL matndan olamiz (Wikipedia katta-kichik harfga sezgir).
    topic = message.strip()
    for w in ("haqida malumot ber", "haqida ayt", "haqida gapir", "haqida", "malumot ber",
              "malumot", "wikipedia", "википедия", "kim edi", "nima edi", "kim bo'lgan",
              "что такое", "кто такой", "расскажи про", "расскажи о", "doda", "iltimos", "menga"):
        topic = re.sub(re.escape(w), " ", topic, flags=re.IGNORECASE)
    topic = " ".join(topic.split()).strip()
    if not topic:
        say("Nima haqida ma'lumot kerak?", lang="uz")
        return
    for lang_code in ("uz", "ru"):
        try:
            url = "https://%s.wikipedia.org/api/rest_v1/page/summary/%s" % (
                lang_code, urllib.parse.quote(topic))
            req = urllib.request.Request(url, headers={"User-Agent": "DODA/1.0"})
            with urllib.request.urlopen(req, timeout=7) as r:
                d = json.loads(r.read().decode("utf-8"))
            extract = d.get("extract", "")
            if extract and d.get("type") != "disambiguation":
                extract = extract.replace("\xa0", " ").replace("​", "")
                short = " ".join(re.split(r"(?<=[.!?])\s", extract)[:2])
                say(short, lang=lang_code)
                return
        except Exception:
            continue
    say("Bu haqida ma'lumot topolmadim.", lang="uz")


def quit_app(message):
    """Ilovani yopadi (quit)."""
    m = _norm(message)
    for name, app in APPS.items():
        if name in m:
            subprocess.run(["osascript", "-e", 'quit app "%s"' % app])
            say(app + " yopildi.", lang="uz")
            return
    say("Qaysi ilovani yopay?", lang="uz")


def get_currency(message):
    """Valyuta kursi (bepul API: open.er-api.com) -> so'mда."""
    m = _norm(message)
    base, name = "USD", "Dollar"
    if "euro" in m or "evro" in m or "евро" in m:
        base, name = "EUR", "Yevro"
    elif "rubl" in m or "рубл" in m or "рубль" in m:
        base, name = "RUB", "Rubl"
    try:
        with urllib.request.urlopen("https://open.er-api.com/v6/latest/" + base, timeout=7) as r:
            d = json.loads(r.read().decode("utf-8"))
        uzs = d["rates"]["UZS"]
        say("Bir " + name + " taxminan " + format(int(uzs), ",").replace(",", " ") + " so'm.", lang="uz")
    except Exception as e:
        print("currency xato:", e)
        say("Valyuta kursini ololmadim.", lang="uz")


def translate_text(message):
    """Matnni tarjima qiladi (bepul Google Translate endpoint)."""
    m = _norm(message)
    target = "en"
    if "ruscha" in m or "рус" in m:
        target = "ru"
    elif "ingliz" in m or "англ" in m or "english" in m:
        target = "en"
    elif "ozbekcha" in m or "узбек" in m:
        target = "uz"
    text = message
    for w in ("tarjima qilib ber", "tarjima qil", "tarjima", "ruschaga", "inglizchaga",
              "ozbekchaga", "o'zbekchaga", "перевести", "переведи", "на русский",
              "на английский", "на узбекский", "doda", "iltimos"):
        text = re.sub(re.escape(w), " ", text, flags=re.IGNORECASE)
    text = " ".join(text.split()).strip()
    if not text:
        say("Nimani tarjima qilay?", lang="uz")
        return
    try:
        url = ("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=%s&dt=t&q=%s"
               % (target, urllib.parse.quote(text)))
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            d = json.loads(r.read().decode("utf-8"))
        translated = "".join(seg[0] for seg in d[0] if seg and seg[0])
        say(translated, lang=target)
    except Exception as e:
        print("translate xato:", e)
        say("Tarjima qilolmadim.", lang="uz")


def calc_math(message):
    """Oddiy matematik amalni hisoblaydi (ovoz bilan aytilgan)."""
    expr = _norm(message)
    for w in ("hisoblab ber", "hisobla", "nechchi boladi", "necha boladi",
              "сколько будет", "posчitay", "posschitay"):
        expr = expr.replace(w, " ")
    for k, v in (("qoshuv", "+"), ("plyus", "+"), ("plus", "+"), ("ayirish", "-"),
                 ("minus", "-"), ("karra", "*"), ("kopaytir", "*"), ("umnozhit", "*"),
                 ("умножить", "*"), ("bolish", "/"), ("bolinsin", "/"), ("razdelit", "/"),
                 ("делить", "/"), ("плюс", "+"), ("минус", "-")):
        expr = expr.replace(k, v)
    expr = re.sub(r"[^0-9+\-*/(). ]", " ", expr).strip()
    if not re.search(r"\d", expr):
        say("Nimani hisoblay?", lang="uz")
        return
    # Daraja (**) katta sonlar bilan dasturni osib qo'yishi mumkin (masalan 9**9**9) — bloklaymiz.
    if re.search(r"\*\s*\*", expr):
        say("Daraja hisobini qo'llab-quvvatlamayman.", lang="uz")
        return
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        say("Javob: " + str(result), lang="uz")
    except Exception:
        say("Buni hisoblolmadim.", lang="uz")


def send_email(message):
    """Email tayyorlaydi — Mail ilovasida to'ldirilgan holda ochiladi (siz jo'natasiz)."""
    body = message.strip()
    low = body.lower()
    for p in ("email yozib yubor", "email yoz", "email yubor", "elektron xat",
              "почту напиши", "имейл", "email"):
        idx = low.find(p)
        if idx != -1:
            body = body[idx + len(p):].strip()
            break
    to, text = "", ""
    mm = re.match(r"(.+?)\s*ga\s+(.+)$", body, re.IGNORECASE | re.DOTALL)
    if mm:
        to, text = mm.group(1).strip(), mm.group(2).strip()
    url = ("mailto:" + urllib.parse.quote(to) + "?subject=" + urllib.parse.quote("DODA")
           + "&body=" + urllib.parse.quote(text))
    subprocess.run(["open", url])
    say("Email tayyorlandi" + ((", " + to + " ga") if to else "") +
        ". Jo'natishдан oldin ko'zdan kechiring.", lang="uz")


def add_calendar_event(message):
    """Kalendarga tadbir qo'shadi (vaqt bilan) yoki Calendar'ni ochadi."""
    delay, title = parse_reminder(message)
    for w in ("kalendarga qosh", "kalendarga yoz", "kalendarga", "kalendar", "tadbir qosh",
              "tadbir", "uchrashuv", "event", "qosh", "yoz"):
        title = title.replace(w, " ")
    title = " ".join(title.split()).strip() or "Tadbir"
    if delay is None:
        subprocess.run(["open", "-a", "Calendar"])
        say("Kalendar ochildi. Tadbir uchun vaqtni ayting, masalan: 'kalendarga qo'sh majlis soat 15 da'.", lang="uz")
        return
    target = dt.datetime.now() + dt.timedelta(seconds=delay)
    safe = title.replace('"', '\\"')
    script = (
        'set d to (current date)\n'
        'set year of d to %d\nset month of d to %d\nset day of d to %d\n'
        'set hours of d to %d\nset minutes of d to %d\nset seconds of d to 0\n'
        'tell application "Calendar"\n'
        '  tell calendar 1\n'
        '    make new event with properties {summary:"%s", start date:d, end date:(d + 3600)}\n'
        '  end tell\n'
        'end tell'
    ) % (target.year, target.month, target.day, target.hour, target.minute, safe)
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode == 0:
        say("Kalendarga qo'shildi: " + title + ", soat " + target.strftime("%H:%M") + ".", lang="uz")
    else:
        print("calendar xato:", r.stderr)
        say("Kalendarga qo'sha olmadim. Calendar ilovasi sozlanganini tekshiring.", lang="uz")


def convert(message):
    """Valyuta miqdori yoki o'lchov birliklarini aylantiradi."""
    m = _norm(message)
    num = re.search(r"(\d+(?:[.,]\d+)?)", m)
    if not num:
        say("Qancha miqdorni aylantiray?", lang="uz")
        return
    val = float(num.group(1).replace(",", "."))
    # Valyuta -> so'm
    cur = cname = None
    if "dollar" in m:
        cur, cname = "USD", "dollar"
    elif "euro" in m or "evro" in m:
        cur, cname = "EUR", "yevro"
    elif "rubl" in m:
        cur, cname = "RUB", "rubl"
    if cur and any(w in m for w in ("som", "sum", "сум")):
        try:
            with urllib.request.urlopen("https://open.er-api.com/v6/latest/" + cur, timeout=7) as r:
                rate = json.loads(r.read().decode("utf-8"))["rates"]["UZS"]
        except Exception:
            say("Kursni ololmadim.", lang="uz")
            return
        pos_som = max(m.rfind("som"), m.rfind("sum"), m.rfind("сум"))
        pos_cur = max(m.rfind(w) for w in ("dollar", "euro", "evro", "rubl", "доллар", "евро", "рубл"))
        if pos_som > pos_cur:  # maqsad so'm: valyuta -> so'm
            say(str(int(val)) + " " + cname + " taxminan " +
                format(int(val * rate), ",").replace(",", " ") + " so'm.", lang="uz")
        else:  # maqsad valyuta: so'm -> valyuta
            say(format(int(val), ",").replace(",", " ") + " so'm taxminan " +
                str(round(val / rate, 2)) + " " + cname + ".", lang="uz")
        return
    # Masofa
    if ("km" in m or "kilometr" in m) and "mil" in m:
        say(str(round(val * 0.621, 1)) + " mil.", lang="uz")
        return
    if "mil" in m:
        say(str(round(val * 1.609, 1)) + " kilometr.", lang="uz")
        return
    if "km" in m or "kilometr" in m:
        say(str(round(val * 0.621, 1)) + " mil.", lang="uz")
        return
    # Og'irlik
    if ("kg" in m or "kilogram" in m) and ("funt" in m or "lb" in m):
        say(str(round(val * 2.205, 1)) + " funt.", lang="uz")
        return
    if "funt" in m or "lb" in m:
        say(str(round(val / 2.205, 1)) + " kilogram.", lang="uz")
        return
    if "kg" in m or "kilogram" in m:
        say(str(round(val * 2.205, 1)) + " funt.", lang="uz")
        return
    # Harorat (yo'nalishни maqsad birligiga qarab aniqlaymiz)
    to_c = any(w in m for w in ("necha selsiy", "selsiyga", "цельси"))
    to_f = any(w in m for w in ("necha farengeyt", "farengeytga", "фаренгейт"))
    if to_c:  # manba Farengeyt -> Selsiy
        say(str(round((val - 32) * 5 / 9, 1)) + " gradus selsiy.", lang="uz")
        return
    if to_f:  # manba Selsiy -> Farengeyt
        say(str(round(val * 9 / 5 + 32, 1)) + " gradus farengeyt.", lang="uz")
        return
    if "farengeyt" in m:  # standart: Farengeyt -> Selsiy
        say(str(round((val - 32) * 5 / 9, 1)) + " gradus selsiy.", lang="uz")
        return
    if "selsiy" in m or "gradus" in m:  # standart: Selsiy -> Farengeyt
        say(str(round(val * 9 / 5 + 32, 1)) + " gradus farengeyt.", lang="uz")
        return
    say("Buni aylantirolmadim.", lang="uz")


def play_song(message):
    """Aytilgan qo'shiq/videoni YouTube'да topib ochadi. Nomi bo'lmasa — umumiy musiqa."""
    q = _norm(message)
    for w in ("qoshigini qoyib ber", "qoshigini qoy", "qoshiqni qoyib ber", "musiqasini qoy",
              "youtubeда oynat", "youtubeда qoy", "youtubeда", "youtubeni", "youtube",
              "video qoyib ber", "videosini qoy", "oynatib ber", "oynat", "qoyib ber",
              "topib qoy", "ijro et", "включи", "поставь", "doda", "iltimos", "menga", "qoy"):
        q = q.replace(w, " ")
    q = " ".join(q.split()).strip()
    if not q or q in ("qoshiq", "musiqa", "qoy", "video"):
        media_control("play")   # umumiy — Apple Music
        return
    open_website("https://www.youtube.com/results?search_query=" + urllib.parse.quote(q),
                 q + " ni YouTube'da ochyapman.")


def add_note(message):
    """Notes ilovasiga qayd yozadi."""
    text = message.strip()
    low = text.lower()
    for p in ("qayd qilib qoy", "qaydga yoz", "qayd qil", "eslatib yoz", "notes yoz",
              "note yoz", "zametka yoz", "заметку", "запиши"):
        idx = low.find(p)
        if idx != -1:
            text = text[idx + len(p):].strip(" :-")
            break
    if not text:
        say("Nima deb yozay?", lang="uz")
        return
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(["osascript", "-e",
                    'tell application "Notes" to make new note with properties {body:"' + safe + '"}'])
    say("Qayd saqlandi: " + text + ".", lang="uz")


def set_voice(message):
    """Ovoz jinsini almashtiradi (erkak/ayol) va saqlaydi."""
    global VOICE_GENDER
    m = _norm(message)
    if any(k in m for k in ("ayol", "ayolcha", "xotin", "женск")):
        VOICE_GENDER = "female"
    elif any(k in m for k in ("erkak", "erkakcha", "мужск")):
        VOICE_GENDER = "male"
    try:
        with open(VOICE_FILE, "w") as f:
            f.write(VOICE_GENDER)
    except Exception:
        pass
    say(("Ayol" if VOICE_GENDER == "female" else "Erkak") + " ovozida gaplashaman.", lang="uz")


# Hissiyotni aniqlash uchun kalit so'zlar (STT xatosiga chidamli — asosiy o'zaklar)
_EMOTION_KEYWORDS = {
    "hursand":  ("hursand", "xursand", "quvonch", "shod", "xushchaqchaq", "весёл", "радост"),
    "hayajon":  ("hayajon", "excited", "qiziqarli ovoz", "воодушев", "восторж"),
    "hafa":     ("hafa", "xafa", "gamgin", "g'amgin", "qaygu", "ma'yus", "grust", "печал"),
    "jahl":     ("jahl", "jahli", "achchiq", "asabiy", "g'azab", "жёстк", "сердит", "зло"),
    "xotirjam": ("xotirjam", "tinch", "hamdard", "yumshoq", "sokin", "спокой", "мягк"),
    "neutral":  ("oddiy", "normal", "tabiiy", "hissiyotsiz", "odatiy", "обычн", "нейтрал"),
}


def set_emotion(message):
    """DODA gapiradigan hissiyot ohangini almashtiradi (hursand/hafa/jahl/xotirjam/hayajon/neutral) va saqlaydi."""
    global CURRENT_EMOTION
    m = _norm(message)
    chosen = None
    for emo, kws in _EMOTION_KEYWORDS.items():
        if any(_norm(k) in m for k in kws):
            chosen = emo
            break
    if chosen is None:
        say("Qaysi hissiyotni xohlaysiz? Hursand, hafa, jahl, xotirjam yoki hayajonli.", lang="uz")
        return
    CURRENT_EMOTION = chosen
    try:
        with open(EMOTION_FILE, "w") as f:
            f.write(CURRENT_EMOTION)
    except Exception:
        pass
    _nomlar = {
        "hursand": "Xursand", "hayajon": "Hayajonli", "hafa": "G'amgin",
        "jahl": "Jahli chiqqan", "xotirjam": "Xotirjam", "neutral": "Oddiy",
    }
    # Yangi hissiyotda javob beramiz (darrov eshitiladi)
    say(_nomlar.get(chosen, chosen) + " ohangda gaplashaman.", lang="uz", emotion=chosen)


# ===== Ekranni boshqarish (klaviatura/oyna — macOS System Events) =====
# Har bir amal uchun AppleScript buyrug'i va o'zbekcha javob.
_SCREEN_ACTIONS = {
    "copy":          ('keystroke "c" using command down',            "Nusxa oldim."),
    "paste":         ('keystroke "v" using command down',            "Joylashtirdim."),
    "cut":           ('keystroke "x" using command down',            "Kesib oldim."),
    "select_all":    ('keystroke "a" using command down',            "Hammasini belgiladim."),
    "undo":          ('keystroke "z" using command down',            "Bekor qildim."),
    "redo":          ('keystroke "z" using {command down, shift down}', "Qaytardim."),
    "save":          ('keystroke "s" using command down',            "Saqladim."),
    "find":          ('keystroke "f" using command down',            "Qidiruvni ochdim."),
    "close_window":  ('keystroke "w" using command down',            "Oynani yopdim."),
    "new_tab":       ('keystroke "t" using command down',            "Yangi ichki oyna ochdim."),
    "new_window":    ('keystroke "n" using command down',            "Yangi oyna ochdim."),
    "minimize":      ('keystroke "m" using command down',            "Oynani yig'ib qo'ydim."),
    "switch_app":    ('keystroke tab using command down',            "Ilovani almashtirdim."),
    "reopen_tab":    ('keystroke "t" using {command down, shift down}', "Yopilgan oynani qaytardim."),
    "zoom_in":       ('keystroke "+" using command down',            "Kattalashtirdim."),
    "zoom_out":      ('keystroke "-" using command down',            "Kichraytirdim."),
    "scroll_down":   ('key code 121',                                "Pastga surdim."),
    "scroll_up":     ('key code 116',                                "Yuqoriga surdim."),
    "scroll_top":    ('key code 115',                                "Boshiga qaytdim."),
    "scroll_bottom": ('key code 119',                                "Oxiriga o'tdim."),
    "enter":         ('key code 36',                                 "Enter bosdim."),
    "escape":        ('key code 53',                                 "Escape bosdim."),
    "backspace":     ('key code 51',                                 "O'chirdim."),
    "tab_key":       ('key code 48',                                 "Tab bosdim."),
}


def _osascript_out(script):
    """AppleScript'ni bajarib, CHIQISH matnini qaytaradi (bo'sh bo'lsa '')."""
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=12)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def system_status():
    """Kompyuterda hozir nima ochiq — qaysi ilovalar va old oynada nima (uzoqdan bilish uchun)."""
    apps = _osascript_out('tell application "System Events" to get name of '
                          '(every process whose background only is false)')
    front = _osascript_out('tell application "System Events" to get name of '
                           'first process whose frontmost is true')
    win = _osascript_out('tell application "System Events" to tell '
                         '(first process whose frontmost is true) to get name of front window')
    qism = []
    if apps:
        qism.append("Ochiq ilovalar: " + apps + ".")
    if front:
        qism.append("Hozir old oynada: " + front + (" — " + win if win else "") + ".")
    say(" ".join(qism) if qism else "Hozir ochiq ilova ko'rinmadi.", lang="uz")


def _new_name(message):
    """'papka yarat loyiham' -> 'loyiham' (trigger va tur so'zlarini olib tashlaydi)."""
    m = _norm(message)
    for tok in ("yangi", "papka", "papkani", "jild", "fayl", "faylni", "file", "folder",
                "yarat", "yaratib", "yarating", "yasa", "yasab", "ber", "och",
                "создай", "создать", "папку", "папка", "файл", "menga", "iltimos", "doda"):
        m = re.sub(r"\b" + tok + r"\b", " ", m)
    return " ".join(m.split()).strip()


def create_folder(message):
    """Ish stolida yangi papka yaratadi."""
    name = _new_name(message)
    if not name:
        say("Papka nomini ayting. Masalan: «loyiha papka yarat».", lang="uz")
        return
    target = os.path.join(os.path.expanduser("~/Desktop"), name)
    try:
        os.makedirs(target, exist_ok=True)
        say("Ish stolida papka yaratdim: " + name, lang="uz")
    except Exception as e:
        say("Papka yaratib bo'lmadi: " + str(e), lang="uz")


def create_file(message):
    """Ish stolida yangi (bo'sh) fayl yaratadi."""
    name = _new_name(message)
    if not name:
        say("Fayl nomini ayting. Masalan: «eslatma.txt fayl yarat».", lang="uz")
        return
    target = os.path.join(os.path.expanduser("~/Desktop"), name)
    try:
        open(target, "a").close()
        say("Ish stolida fayl yaratdim: " + name, lang="uz")
    except Exception as e:
        say("Fayl yaratib bo'lmadi: " + str(e), lang="uz")


def close_finder():
    """Barcha ochiq papka (Finder) oynalarini yopadi."""
    if _run_osascript('tell application "Finder" to close every window'):
        say("Barcha papka oynalarini yopdim.", lang="uz")


def system_report():
    """Birlashtirilgan tizim holati: batareya + CPU + RAM."""
    say(mac_system.report(), lang="uz")


def read_clipboard():
    """Almashtirish buferidagi (clipboard) matnni o'qib beradi."""
    txt = mac_system.clipboard_text()
    if not txt:
        say("Almashtirish buferi hozir bo'sh.", lang="uz")
    else:
        qisqa = txt if len(txt) <= 500 else txt[:500] + "…"
        say("Buferda quyidagi matn bor: " + qisqa, lang="uz")


def _run_osascript(script):
    """AppleScript'ni bajaradi. Accessibility ruxsati kerak (birinchi marta System Settings'da yoqiladi)."""
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if r.returncode != 0 and "assistive" in (r.stderr or "").lower():
            say("Ekranni boshqarish uchun ruxsat kerak. Tizim sozlamalari, "
                "Maxfiylik va xavfsizlik, Foydalanish imkoniyati bo'limidan Terminalga ruxsat bering.", lang="uz")
            return False
        return r.returncode == 0
    except Exception as e:
        print("osascript xato:", e)
        return False


def screen_control(action):
    """Ekran/klaviatura amalini bajaradi (nusxa, joylashtir, scroll, oyna h.k.)."""
    entry = _SCREEN_ACTIONS.get(action)
    if not entry:
        return
    script, reply = entry
    if _run_osascript('tell application "System Events" to ' + script):
        say(reply, lang="uz")


def type_text(message):
    """DODA klaviaturadan matn yozadi. Masalan: 'yozib ber salom dunyo'."""
    # Trigger so'zdan keyingi matnni asl holida (katta-kichik saqlab) olamiz
    low = message.lower()
    triggers = ["klaviaturada yoz", "matn yoz", "yozib yubor", "yozib ber", "yozib qoy", "type", "напиши", "печатай"]
    pos, tlen = -1, 0
    for t in triggers:
        i = low.find(t)
        if i != -1 and (pos == -1 or i < pos):
            pos, tlen = i, len(t)
    if pos == -1:
        say("Nima yozay?", lang="uz")
        return
    text = message[pos + tlen:].lstrip(" :-—,").rstrip()
    if not text:
        say("Nima yozay?", lang="uz")
        return
    # AppleScript uchun maxsus belgilarni himoyalaymiz
    safe = text.replace("\\", "\\\\").replace('"', '\\"')
    if _run_osascript(f'tell application "System Events" to keystroke "{safe}"'):
        say("Yozdim.", lang="uz")


# ===== Ko'rish (vision) — kamera/ekran + Claude tushunishi =====
VISION_MAX_TOKENS = 400
VISION_SYSTEM_PROMPT = (
    "Sen DODA'ning ko'zisan. Berilgan rasmda nima ko'rayotganingni O'ZBEK tilida "
    "QISQA va aniq ayt (javob ovoz orqali o'qiladi). Narsalar, ovqat, buyumlar, "
    "foydalanuvchi qilayotgan amalni tasvirla. MUHIM: odamlarning shaxsini (kimligini) "
    "aniqlashga URINMA — faqat ko'rinishini tasvirla (masalan 'bir kishi turibdi'). "
    "Markdown yoki emoji ishlatma."
)


def _describe_image_claude(image_path, question):
    """Rasmni Claude'ga yuborib, nima ko'rinayotganini o'zbekcha qaytaradi (multimodal)."""
    from vision import image_to_base64
    data, media_type = image_to_base64(image_path)
    client = _get_claude()
    resp = client.messages.create(
        model=CHAT_MODEL,
        max_tokens=VISION_MAX_TOKENS,
        system=VISION_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                {"type": "text", "text": question or "Bu rasmda nimani ko'ryapsan?"},
            ],
        }],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def _vision_question(message):
    """Foydalanuvchi savolini ajratadi ('bu qanaqa ovqat?' kabi), yo'q bo'lsa None."""
    low = _norm(message)
    # Sof "qara/ko'r" buyrug'i bo'lsa aniq savol yo'q
    generic = ("kameraga qara", "nima koryapsan", "atrofimga qara", "oldimda nima",
               "ekranda nima", "ekranni or", "ekranni oqi", "bu nima", "nima bu")
    for g in generic:
        if _norm(g) in low:
            return None
    return message  # foydalanuvchi aniq savol bergan bo'lsa o'shani uzatamiz


def _capture_and_see(source, message):
    """source='camera' yoki 'screen': rasm oladi, Claude bilan tushuntiradi."""
    from vision import capture_camera, capture_screen
    if source == "camera":
        say("Kameraga qarayapman.", lang="uz")
        path = capture_camera()
        fail = "Kamerani ocholmadim. Kamera ruxsatini tekshiring (Sozlamalar, Maxfiylik, Kamera)."
    else:
        say("Ekranga qarayapman.", lang="uz")
        path = capture_screen()
        fail = "Ekran suratini ololmadim. Ekranni yozib olish ruxsatini bering (Sozlamalar, Maxfiylik, Ekranni yozib olish)."
    if not path:
        say(fail, lang="uz")
        return
    try:
        if not AI_CHAT_ENABLED:
            say("Rasmni oldim. Uni tushunish uchun Claude kerak — birinchi avgustda ishga tushadi.", lang="uz")
            return
        desc = _describe_image_claude(path, _vision_question(message))
        say(desc or "Aniq ko'ra olmadim.", lang="uz")
    except Exception as e:
        print("vision xato:", e)
        say("Kechirasiz, hozir ko'ra olmadim.", lang="uz")
    finally:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _extract_person_name(message):
    """'eslab qol bu Alisher' / 'yuzini eslab qol bu Diyor' dan ismni ajratadi (ism odatda oxirda)."""
    t = message
    t = re.sub(r"(?i)\b(eslab qol|eslab qolgin|eslab ol|bu kishi|bu odam|bu|tanishtiraman|"
               r"yuzini|yuzi|yuz|kishini|odamni|ismi|nomi|deb chaqir|запомни|это|этого)\b", " ", t)
    t = " ".join(t.split()).strip(" ,.-")
    # Ism odatda gap oxirida keladi -> oxirgi so'zni olamiz
    return t.split()[-1] if t else ""


def see_and_remember(message):
    """Kameradan yuzni ism bilan eslab qoladi (lokal face_recognition kutubxonasi kerak)."""
    from vision import capture_camera, remember_face
    name = _extract_person_name(message)
    if not name:
        say("Kimni eslab qolay? Ismini ayting.", lang="uz")
        return
    say(name + "ni ko'rish uchun kameraga qarayapman.", lang="uz")
    path = capture_camera()
    if not path:
        say("Kamerani ocholmadim.", lang="uz")
        return
    try:
        ok, msg = remember_face(name, path)
        say(msg, lang="uz")
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def see_who(message):
    """Kameradagi odamlarni saqlangan yuzlar bilan taniydi (lokal)."""
    from vision import capture_camera, identify_faces
    path = capture_camera()
    if not path:
        say("Kamerani ocholmadim.", lang="uz")
        return
    try:
        names, err = identify_faces(path)
        if err:
            say(err, lang="uz")
        elif not names:
            say("Hech kimni ko'rmadim.", lang="uz")
        else:
            tanish = [n for n in names if n != "notanish"]
            if tanish:
                say("Ko'rdim: " + ", ".join(tanish), lang="uz")
            else:
                say("Bir kishi bor, lekin uni tanimadim.", lang="uz")
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _clean_spoken_name(text):
    """Aytilgan javobdan ismni ajratadi: «mening ismim Ali» / «men Dilnoza» / «Ali» -> ism.
    So'z-chegarasi bilan olib tashlaydi (ism ichidagi bo'g'inni buzmaydi: «Bobur» butun qoladi)."""
    t = _norm(text or "")
    stop = ("mening ismim", "ismim", "meni", "men", "deb chaqir", "chaqir", "deb", "chaqiring",
            "atim", "otim", "ismi", "menга", "меня зовут", "меня", "зовут", "я")
    for w in stop:
        t = re.sub(r"\b" + re.escape(w) + r"\b", " ", t)
    t = " ".join(t.split()).strip(" ,.-")
    if not t:
        return ""
    return t.split()[-1].capitalize()   # ism odatda oxirida keladi


def meet_and_greet(message=""):
    """Kameradagi odamlarni taniydi (ko'p odam ham). Notanish bo'lsa — DODA o'zini
    tanishtirib, ismini so'raydi va yuzini eslab qoladi. «Yonimда yangi odam» stsenariysi."""
    from vision import capture_camera, identify_faces, remember_face
    path = capture_camera()
    if not path:
        say("Kamerani ocholmadim. Kamera ruxsatini tekshiring.", lang="uz")
        return
    try:
        names, err = identify_faces(path)
        if err:
            say(err, lang="uz")
            return
        if not names:
            say("Hozir kamerada hech kimni ko'rmayapman.", lang="uz")
            return
        known = [n for n in names if n != "notanish"]
        unknown = names.count("notanish")
        # Kim borligini aytamiz
        parts = []
        if known:
            parts.append("tanidim: " + ", ".join(known))
        if unknown:
            parts.append(("%d ta notanish odam" % unknown) if unknown > 1 else "bitta notanish odam")
        say(("Ko'rdim — " + "; ".join(parts) + ".") if parts else "Odam ko'rmadim.", lang="uz")

        # Notanish bo'lsa — tanishamiz (faqat desktop/mikrofon rejimida so'ray olamiz)
        if unknown >= 1 and _capture is None:
            say("Assalomu alaykum! Men DODA — Muhammadxo'ja yaratgan ovozli yordamchiman. "
                "Ismingiz nima?", lang="uz")
            ans = listen()
            nm = _clean_spoken_name(ans)
            if not nm:
                say("Ismingizni tushunmadim, keyinroq tanishamiz.", lang="uz")
                return
            ok, _msg = remember_face(nm, path, only_unknown=True)   # notanish yuzni saqlaydi
            if ok:
                say("Tanishganimdan xursandman, " + nm + "! Endi sizni eslab qoldim.", lang="uz")
            else:
                say("Yuzingizni aniq ololmadim, iltimos kameraga qarab qaytadan urinib ko'ring.", lang="uz")
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def _wants_remember_me(m):
    """«meni eslab qol» niyatini STT biroz buzsa ham tutadi (m — normallashtirilган).
    «eslab/yodla» + o'zi haqида ishora (men/meni/o'zim/yuzim) bo'lsa TRUE — lekin
    «eslab qol bu ...» (boshqa odam) EMAS. Vaqtли eslatma («eslat») bu emas."""
    if "eslab" not in m and "yodla" not in m:
        return False
    if "bu " in m or m.endswith(" bu") or m == "bu":   # «eslab qol bu Ali» -> boshqa odam
        return False
    return any(w in m.split() for w in ("men", "meni", "ozim", "ozimni", "yuzim", "yuzimni", "meniyam"))


def remember_me(message=""):
    """«Meni eslab qol» — foydalanuvchining O'Z yuzini ism bilan yodlaydi.
    Ism: xabarda bo'lsa undan («meni eslab qol Bobur»), bo'lmasa saqlangan ismdan
    (~/.doda_user_name), bo'lmasa desktop'да so'raladi."""
    from vision import capture_camera, remember_face
    # Xabar oxirida ism bormi? (buyruq so'zlarини olib tashlab qaraymiz)
    cleaned = re.sub(r"(?i)\b(meni|o'zimni|ozimni|mening|yuzimni|yuzim|eslab qol(gin)?|eslab ol|"
                     r"yodla(b ol)?|tanib ol|tani|bu|deb chaqir|запомни|меня)\b", " ", message)
    cleaned = " ".join(cleaned.split()).strip(" ,.-")
    nm = cleaned.split()[-1].capitalize() if cleaned else ""
    if not nm:
        nm = _load_user_name() or ""
    if not nm:
        if _capture is None:          # desktop (mikrofon) — ismini so'raymiz
            say("Ismingiz nima? Yuzingizni shu ism bilan yodlab qolaman.", lang="uz")
            nm = _clean_spoken_name(listen())
        if not nm:
            say("Ismingizni ham ayting: «meni eslab qol Bobur» deb.", lang="uz")
            return
    say(nm + ", kameraга qarab turing — yuzingizni yodlab olyapman.", lang="uz")
    path = capture_camera()
    if not path:
        say("Kamerani ocholmadim. Kamera ruxsatini tekshiring.", lang="uz")
        return
    try:
        ok, msg = remember_face(nm, path)
        say(("Yodlab qoldim, " + nm + "! Endi sizni yuzingizdan tanийman.") if ok else msg, lang="uz")
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


def vision_control(message, arg):
    """Ko'rish buyruqlarini yo'naltiradi."""
    if arg == "camera":
        _capture_and_see("camera", message)
    elif arg == "screen":
        _capture_and_see("screen", message)
    elif arg == "remember":
        see_and_remember(message)
    elif arg == "rememberme":
        remember_me(message)
    elif arg == "identify":
        see_who(message)
    elif arg == "meet":
        meet_and_greet(message)


_KOMANDA_HANDLERS = {
    "media": media_control,
    "system": system_control,
    "time": time_info,
    "dev": run_dev,
}


# ===== Jonli buyruq qo'shish (ovoz/bot orqali o'rgatish) =====
_TEACH_APP = ("ilova qosh", "ilova qo'sh", "ilovani qosh", "ilovani qo'sh", "yangi ilova qosh", "yangi ilova qo'sh", "добавь приложение")
_TEACH_SITE = ("sayt qosh", "sayt qo'sh", "saytni qosh", "saytni qo'sh", "yangi sayt qosh", "yangi sayt qo'sh", "добавь сайт")
_TEACH_FOLDER = ("papka qosh", "papka qo'sh", "jild qosh", "jild qo'sh", "добавь папку")
_TEACH_JAVOB = ("javob qosh", "javob qo'sh", "gap orgat", "gap o'rgat", "soz orgat", "so'z o'rgat", "menga javob qosh", "menga javob qo'sh", "добавь ответ", "научись отвечать")
_TEACH_LIST = ("qoshilgan buyruq", "qo'shilgan buyruq", "mening buyruqlarim", "qanaqa buyruq qoshdim", "qanday buyruq qoshdim", "custom buyruq", "мои команды")
_TEACH_REMOVE = ("buyruqni ochir", "buyruqni o'chir", "buyruq ochir", "buyruq o'chir", "qoshgan buyruqni ochir", "qo'shgan buyruqni o'chir", "удали команду")


def _is_cyrillic(text):
    return any("Ѐ" <= ch <= "ӿ" for ch in text)


def _teach_after(raw, verbs):
    """Matndagi buyruq iborasidan KEYINGI qismni qaytaradi (so'z-bo'yicha, apostroflarga chidamli)."""
    words = raw.split()
    low = [_norm(w) for w in words]
    for v in verbs:
        vw = _norm(v).split()
        L = len(vw)
        for i in range(len(low) - L + 1):
            if low[i:i + L] == vw:
                return " ".join(words[i + L:]).strip()
    return raw.strip()


def _rebuild_rules():
    """Foydalanuvchi javob qo'shgach RULES'ni qayta quradi (yangi javob darhol ishlasin)."""
    global RULES, JAVOBLAR
    import javoblar as _jv
    JAVOBLAR = _jv.load_javoblar()
    RULES = [(_kw, _make_reply(_resp, _lang)) for _kw, _resp, _lang in JAVOBLAR]


def _is_teach(m):
    return any(_norm(k) in m for k in
               (_TEACH_APP + _TEACH_SITE + _TEACH_FOLDER + _TEACH_JAVOB + _TEACH_LIST + _TEACH_REMOVE))


def handle_teach(message):
    """'ilova/sayt/papka/javob qo'sh <so'z> = <qiymat>' — buyruqni JSON'ga yozadi va darhol yoqadi."""
    raw = message.strip()
    low = _norm(raw)

    # Qo'shilganlar ro'yxati
    if any(_norm(k) in low for k in _TEACH_LIST):
        lst = foydalanuvchi.summary()
        if not lst:
            say("Siz hali hech qanday buyruq qo'shmagansiz.", lang="uz")
        else:
            say("Siz qo'shgan buyruqlar: " + "; ".join(lst), lang="uz")
        return True

    # O'chirish
    if any(_norm(k) in low for k in _TEACH_REMOVE):
        target = _teach_after(raw, _TEACH_REMOVE)
        if not target:
            say("Qaysi buyruqni o'chiray? Kalit so'zini ayting.", lang="uz")
            return True
        n = foydalanuvchi.remove(target)
        buyruq_baza.reload()
        _rebuild_rules()
        if n:
            say("O'chirildi: '" + target + "'.", lang="uz")
        else:
            say("'" + target + "' nomli qo'shilgan buyruq topilmadi.", lang="uz")
        return True

    # Qo'shish (app/sayt/papka/javob) — "so'z = qiymat"
    for verbs, kind in ((_TEACH_APP, "app"), (_TEACH_SITE, "site"),
                        (_TEACH_FOLDER, "folder"), (_TEACH_JAVOB, "javob")):
        if any(_norm(k) in low for k in verbs):
            body = _teach_after(raw, verbs)
            if "=" not in body:
                say("Iltimos shu ko'rinishda ayting: '<so'z> teng <qiymat>'. "
                    "Masalan: 'sayt qo'sh olx teng olx.uz'.", lang="uz")
                return True
            left, right = body.split("=", 1)
            left, right = left.strip(), right.strip()
            if not left or not right:
                say("So'z yoki qiymat bo'sh qoldi. Masalan: 'ilova qo'sh telefon = Phone'.", lang="uz")
                return True
            if kind == "app":
                foydalanuvchi.add_app(left, right)
                msg = "Saqladim ✅ Endi «" + left + " och» desangiz, " + right + " ilovasi ochiladi."
            elif kind == "site":
                foydalanuvchi.add_site(left, right)
                msg = "Saqladim ✅ Endi «" + left + " och» desangiz, " + right + " sayti ochiladi."
            elif kind == "folder":
                foydalanuvchi.add_folder(left, right)
                msg = "Saqladim ✅ Endi «" + left + " och» desangiz, " + right + " papkasi ochiladi."
            else:  # javob
                lang = "ru" if _is_cyrillic(right) else "uz"
                foydalanuvchi.add_javob([left.lower()], [right], lang)
                _rebuild_rules()
                msg = "Yodladim: '" + left + "' desangiz, '" + right + "' deb javob beraman."
            buyruq_baza.reload()
            say(msg, lang="uz")
            return True

    return False


def set_listening(mode):
    """Ovoz rejimida mikrofon tinglashini yoqadi/o'chiradi."""
    global INPUT_MODE
    if mode == "stop":
        INPUT_MODE = "text"
        say("Xo'p, ovozdan tinglashni to'xtatdim. Buyruqni yozib bering yoki 'meni tingla' deng.", lang="uz")
    else:  # start
        INPUT_MODE = "hybrid"
        say("Yaxshi, yana tinglayapman. Gapiravering!", lang="uz")


def try_komanda(message):
    """buyruq_baza.py dagi KOMANDALAR ro'yxati bo'yicha aniq harakat qiladi."""
    m = _norm(message)
    for keywords, typ, arg in KOMANDALAR:
        if any(_norm(k) in m for k in keywords):
            if typ == "reply":
                say_random(arg, "uz")
            elif typ == "timer":
                start_timer(message)
            elif typ == "sms":
                send_sms(message)
            elif typ == "telegram":
                send_telegram(message)
            elif typ == "call":
                make_call(message)
            elif typ == "weather":
                get_weather(message)
            elif typ == "wiki":
                get_wiki(message)
            elif typ == "quit":
                quit_app(message)
            elif typ == "email":
                send_email(message)
            elif typ == "calendar":
                add_calendar_event(message)
            elif typ == "convert":
                convert(message)
            elif typ == "note":
                add_note(message)
            elif typ == "voice":
                set_voice(message)
            elif typ == "emotion":
                set_emotion(message)
            elif typ == "screen":
                screen_control(arg)
            elif typ == "type":
                type_text(message)
            elif typ == "vision":
                vision_control(message, arg)
            elif typ == "news":
                get_news(message)
            elif typ == "play":
                play_song(message)
            elif typ == "prayer":
                get_prayer_times(message)
            elif typ == "crypto":
                get_crypto(message)
            elif typ == "hijri":
                get_hijri_date(message)
            elif typ == "currency":
                get_currency(message)
            elif typ == "translate":
                translate_text(message)
            elif typ == "math":
                calc_math(message)
            elif typ == "stopwatch":
                handle_stopwatch(arg)
            elif typ == "listen":
                set_listening(arg)
            elif typ == "status":
                system_status()
            elif typ == "makefolder":
                create_folder(message)
            elif typ == "makefile":
                create_file(message)
            elif typ == "closefolders":
                close_finder()
            elif typ == "syscheck":
                system_report()
            elif typ == "clipboard":
                read_clipboard()
            else:
                _KOMANDA_HANDLERS[typ](arg)
            return True
    return False


def try_nlu(message):
    """Ilova / sayt / papka / qidiruv niyatini aniqlab, harakat qiladi."""
    m = _norm(message)

    # 1) Qidiruv
    if any(w in m for w in ("qidir", "izla", "search", "найди", "поиск")):
        url = SEARCH_ENGINES["google"]
        for name, u in SEARCH_ENGINES.items():
            if name in m:
                url = u
                break
        query = m
        for name in SEARCH_ENGINES:
            query = re.sub(name + r"[a-zа-яё]*", " ", query)
        query = re.sub(r"\b(qidirib ber|qidirib|qidir|izlab ber|izlab|izla|search|найди|поиск)\b", " ", query)
        query = re.sub(r"\b(da|да|ni|ни|dan|ga|doda|iltimos|menga)\b", " ", query)
        query = " ".join(query.split()).strip()
        if not query:
            say("Nimani qidiray?", lang="uz")
            return True
        open_website(url + urllib.parse.quote(query), "Qidiryapman.")
        return True

    # 2) Saytlar
    for name, url in SITES.items():
        if name in m:
            open_website(url, name + " ochilyapti.")
            return True

    # 3) Ilovalar
    for name, app in APPS.items():
        if name in m:
            open_app(app, app + " ochilyapti.")
            return True

    # 4) Papkalar (butun so'z sifatida — "foto" "fotoshop" ichiga tushmasligi uchun)
    for name, path in FOLDERS.items():
        if _word_in(name, m):
            open_folder(path, name + " papkasi ochilyapti.")
            return True

    # 5) Zaxira: "<noma'lum nom> och" -> ilova sifatida, bo'lmasa brauzerdan qidirib ochamiz
    if any(w in m for w in ("och", "ochib", "ishga tushir", "открой", "запусти")):
        target = _extract_open_target(message)
        if target:
            open_app_or_web(target)
            return True

    return False


_UZ_SUFFIX = r"(ni|ning|ga|da|dan|lar|larni|im|ing|i)?"


def _word_in(name, text):
    """name matnda BUTUN so'z sifatida bormi (o'zbekcha qo'shimchalar bilan)? 'foto' 'fotoshop' ga tushmaydi."""
    return re.search(r"\b" + re.escape(name) + _UZ_SUFFIX + r"\b", text) is not None


def _extract_open_target(message):
    """"instagram och", "menga telegram ochib ber" dan ochiladigan nomni ajratib oladi."""
    t = _norm(message)
    # Ochish fe'llari va ortiqcha so'zlarni olib tashlaymiz
    t = re.sub(r"\b(ochib ber|ochib bergin|ochib|ochgin|ochsang|och|ishga tushir|ishga tushirib ber|"
               r"открой|запусти|включи)\b", " ", t)
    t = re.sub(r"\b(menga|iltimos|doda|ilovani|ilova|dastur|dasturni|ni|ni ni|please|мне|пожалуйста)\b", " ", t)
    return " ".join(t.split()).strip()


# ===== "Yaqin so'z" (fuzzy) tuzatish — STT xatolarини kechiradi =====
_VOCAB = None


def _get_vocab():
    """Barcha buyruq so'zlaridan lug'at yig'adi (bir marta)."""
    global _VOCAB
    if _VOCAB is None:
        v = set()
        for d in (APPS, SITES, FOLDERS, SEARCH_ENGINES):
            for k in d:
                v.update(_norm(k).split())
        for kws, _t, _a in KOMANDALAR:
            for k in kws:
                v.update(_norm(k).split())
        try:
            from javoblar import JAVOBLAR as _J
        except Exception:
            _J = []
        for e in _J:
            for k in e[0]:
                v.update(_norm(k).split())
        v.update(["eslat", "budilnik", "xayr", "parol", "ismim", "kimman", "eslatib",
                  "qidir", "doda", "salom", "havo", "nechi", "qancha", "menga"])
        # Himoyalangan qisqa so'zlar (tuzatilmasin)
        _PROTECTED = {"och", "yoq", "qil", "ber", "bor", "tur", "ayt", "gapir",
                      "kim", "nima", "men", "sen", "yop"}
        v.update(_PROTECTED)
        _VOCAB = {w for w in v if len(w) >= 3}
    return _VOCAB


def _autocorrect(message):
    """Har bir so'zni lug'atdagi eng yaqin so'zga tuzatadi (STT sal xato yozsa ham)."""
    vocab = _get_vocab()
    out = []
    for w in _norm(message).split():
        if len(w) <= 2 or w.isdigit() or w in vocab:
            out.append(w)
        else:
            match = difflib.get_close_matches(w, vocab, n=1, cutoff=0.74)
            out.append(match[0] if match else w)
    return " ".join(out)


def _is_telegram_send(message):
    """«telegramda/telegramga <kim> ga <matn> yubor» — Telegramда xabar yuborish buyrug'imi?
    «telegram och/yop» (ilovani ochish) bunga KIRMAYDI."""
    m = _norm(message)
    if "telegram" not in m:
        return False
    # ilovani ochish/yopish — bu emas
    if any(k in m for k in ("telegram och", "telegramni och", "telegram ochib",
                            "telegramni yop", "telegram yop")):
        return False
    # yuborish niyati + kimgadir ("... ga ...") bo'lishi kerak
    if not any(w in m for w in ("yubor", "jonat", "yoz", "xabar")):
        return False
    return re.search(r"\wga\s+\w|\w ga \w", m) is not None


def _dispatch(massage):
    """Buyruqni aniqlab bajaradi. Bajarilsa True, aks holda False."""
    m = _norm(massage)
    words = m.split()

    # Jonli buyruq o'rgatish (ilova/sayt/papka/javob qo'sh, o'chir, ro'yxat) — hamma narsadan oldin.
    if _is_teach(m):
        return handle_teach(massage)

    # Xayrlashuv — qaysi tilda aytilsa, o'sha tilda javob (o'zbekcha "xayr" -> o'zbekcha).
    if ("xayr" in words) or any(k in m for k in ("bye", "goodbye", "korishguncha",
                                                 "dasturdan chiq", "ishni tugat", "dasturni tark", "chiqib ket")):
        say_random(["Xayr! Yaxshi qoling.", "Ko'rishguncha, omad!", "Xayr, o'zingizni ehtiyot qiling."], lang="uz")
        raise SystemExit
    if any(k in m for k in ("пока", "прощай", "до свидания", "увидимся",
                            "выход из программы", "закрой программу", "выйти из программы", "заверши работу")):
        say_random(["Пока! Хорошего дня.", "До свидания!", "Увидимся!"], lang="ru")
        raise SystemExit

    if any(k in m for k in ("parol ber", "botga kirishga parol", "bot paroli", "botga parol", "kirish paroli")):
        generate_bot_password()
        return True

    if any(k in m for k in ("eslatmalarim", "eslatmalar royxati", "faol eslatma",
                            "qanday eslatmalar", "eslatmalarni korsat", "мои напоминания")):
        list_reminders()
        return True

    if any(k in m for k in ("alarmni bekor", "budilnikni ochir", "budilnikni bekor",
                            "eslatmani ochir", "eslatmani bekor", "eslatmalarni ochir",
                            "отмени будильник", "удали напоминание")):
        cancel_reminders()
        return True

    if handle_user_name(massage):
        return True

    # Takroriy eslatma (har kuni / ish kunlari / muayyan kunlar)
    if is_recurring(massage):
        parsed = parse_recurring(massage)
        if parsed:
            days, hh, mm, note = parsed
            add_recurring("local", days, hh, mm, note)
            say("Yaxshi, " + _days_name(days) + " soat " + ("%02d:%02d" % (hh, mm)) +
                " da eslataman: " + note + ".", lang="uz")
        else:
            say("Takroriy eslatma uchun kun va vaqtni ayting.", lang="uz")
        return True

    if is_reminder(massage):
        add_reminder(massage)
        return True

    # Telegram orqali xabar yuborish ("telegramda Onamga salom yubor") —
    # "telegram och" (ilovani ochish) bilan chalkashmasligi uchun ANIQ tekshiramiz
    if _is_telegram_send(massage):
        send_telegram(massage)
        return True

    # STT «meni eslab qol»ni ko'pincha buzib yozadi (masalan «men eslab», «yuzimni es lab»).
    # Aniq buyruqlardan keyin, lekin NLU/AI'dan oldin — yumshoq (bardoshli) tutamiz.
    if _wants_remember_me(m):
        remember_me(massage)
        return True

    if try_komanda(massage):
        return True

    if try_nlu(massage):
        return True

    for keywords, action in RULES:
        if any(_norm(keyword) in m for keyword in keywords):
            action()
            return True

    return False


# ===== Markaziy xatolik boshqaruvi (qulab tushmaslik + Telegram'ga xabar) =====
ERRORS_LOG = os.path.expanduser("logs/.doda_errors.log")   # /log shu yerdan o'qiydi
_last_err_notify = [0.0]


def _notify_owner(text):
    """Xatolik haqida egaga Telegram orqali TO'G'RIDAN xabar (qaysi jarayondan bo'lsa ham)."""
    try:
        tok = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not tok:
            tok = open(os.path.expanduser("~/.doda_bot_token")).read().strip()
    except Exception:
        return
    if not tok:
        return
    try:
        users = [x for x in open(os.path.expanduser("~/.doda_bot_users")).read().split()
                 if x.strip().isdigit()]
    except Exception:
        users = []
    for uid in users:
        try:
            data = urllib.parse.urlencode({"chat_id": uid, "text": text}).encode()
            urllib.request.urlopen(
                "https://api.telegram.org/bot%s/sendMessage" % tok, data=data, timeout=10)
        except Exception:
            pass


def _report_error(where, exc):
    """Xatoni jurnalgа yozadi va (cheklangan holda) egaga Telegram xabar yuboradi."""
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "%s [%s] %s: %s" % (stamp, where, type(exc).__name__, exc)
    print("XATO:", line)
    try:
        if os.path.exists(ERRORS_LOG) and os.path.getsize(ERRORS_LOG) > 200 * 1024:
            open(ERRORS_LOG, "w").close()   # juda katta bo'lsa tozalaymiz
        with open(ERRORS_LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n" + traceback.format_exc() + "\n")
    except Exception:
        pass
    now = time.time()
    if now - _last_err_notify[0] >= 120:    # 2 daqiqada bir marta (spam bo'lmasin)
        _last_err_notify[0] = now
        _notify_owner("⚠️ Xatolik: " + line[:180] + "\n/log bilan batafsil ko'ring.")


def handle_massage(massage):
    """Buyruqni himoyalangan holda bajaradi — handler qulasa ham dastur to'xtamaydi."""
    try:
        _handle_core(massage)
    except SystemExit:
        raise                                # xayrlashuv -> dastur atayin chiqadi
    except Exception as e:
        _report_error("buyruq: " + str(massage)[:60], e)
        try:
            say("Kutilmagan xatolik yuz berdi, lekin ishlashda davom etaman.", lang="uz")
        except Exception:
            pass


def _handle_core(massage):
    # 1) To'g'ridan-to'g'ri
    if _dispatch(massage):
        return
    # 2) "Yaqin so'z" bilan tuzatib qayta urinish (STT sal xato yozsa ham topadi)
    corrected = _autocorrect(massage)
    if corrected != _norm(massage) and _dispatch(corrected):
        print("(tuzatildi:", corrected, ")")
        return
    # 3) Hech nima mos kelmadi -> tushunmadim / AI
    if not AI_CHAT_ENABLED:
        say("Bu buyruqni tushunmadim.", lang="uz")
        return
    # AI yoqilgan, lekin kalit hali qo'yilmagan bo'lsa -> qo'rqinchli auth xatosi bermaymiz
    if not _load_api_key():
        say("Bu buyruqni tushunmadim. (AI suhbat uchun Claude kaliti hali qo'yilmagan.)", lang="uz")
        return
    # 3a) Agent so'rovimi (fayl/kod/terminal ishi)? -> asboblar bilan bajaramiz
    if AGENT_MODE_ENABLED and _is_agent_request(massage):
        try:
            reply, lang = agent_with_claude(massage)
            say(reply, lang=lang)
        except Exception as e:
            print("Agent xatosi:", e)
            say("Kechirasiz, bu vazifani bajara olmadim.", lang="uz")
        return
    # 3b) Oddiy erkin suhbat
    try:
        reply, lang = chat_with_claude(massage)
        say(reply, lang=lang)
    except Exception as e:
        print("Claude xatosi:", e)
        say("Kechirasiz, hozir javob bera olmayapman.", lang="uz")


def _is_agent_request(massage):
    """Xabar agent (fayl/kod/terminal) ishimi yoki oddiy suhbatmi — kalit so'zlar bilan aniqlaydi."""
    low = _norm(massage)
    return any(_norm(t) in low for t in AGENT_TRIGGERS)


def _transcribe_audio(audio):
    """Audio -> matn (listen()dagi kabi: avval online Google, ishlamasa offline Whisper)."""
    try:
        t = _recognize_online(audio)
        if t:
            return t
    except sr.RequestError:
        pass
    except Exception:
        pass
    try:
        return _recognize_offline(audio)
    except Exception:
        return ""


def _transcribe_wake(audio):
    """Wake-so'z + buyruq uchun. ONLINE (Google) BIRINCHI — o'zbekchani Whisper'дан ancha
    yaxshi va tezroq tanidi; `operation_timeout=6` tufayli endi osilib qolmaydi (ilgari
    osilardi, shu sabab vaqtincha offline-birinchi edi). Bo'sh/xato bo'lsa -> offline
    Whisper (for_wake: qisqa so'z uchun VAD-siz, til-avtomatik)."""
    try:
        t = _recognize_online(audio)
        if t:
            return t
    except sr.RequestError:
        pass
    except Exception:
        pass
    try:
        return _recognize_offline(audio, for_wake=True)
    except Exception:
        return ""


_io_lock = threading.Lock()   # matn va ovoz oqimi bir vaqtда handle_massage chaqirmasin


def _handle_locked(msg):
    """handle_massage'ni qulf bilan chaqiradi (matn va ovoz oqimi to'qnashmasin)."""
    with _io_lock:
        handle_massage(msg)


def _wake_session():
    """«Doda» degach ochiladigan SUHBAT SESSIYASI: buyruqlarни ketma-ket qabul qiladi
    (har safar «Doda» demasangiz ham). WAKE_SESSION_SILENCE soniya JIM bo'lsangiz —
    tinglashni bas qiladi va yana «Doda» kutiladi. Har buyruqdan keyin jimlik hisobi
    qaytadan boshlanadi (davomli suhbat)."""
    while True:
        try:
            with sr.Microphone() as source:
                audio = _recognizer.listen(source, timeout=WAKE_SESSION_SILENCE,
                                           phrase_time_limit=PHRASE_TIME_LIMIT)
        except sr.WaitTimeoutError:
            print("🔇 %ds jim bo'ldingiz — tinglashni to'xtatdim. Qayta «Doda» deng."
                  % WAKE_SESSION_SILENCE)
            return
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            return
        cmd = _transcribe_audio(audio)
        if cmd:
            print("🎙  ", cmd)
            _handle_locked(cmd)      # xayr -> SystemExit (yuqoriga o'tadi, dastur chiqadi)


def wake_loop():
    """Uyg'otkich so'z rejimi: JIMLIKDA tinglamaydi (faqat gapirilganда ishlaydi).
    «Doda» eshitsa -> «labbay» deydi va SUHBAT SESSIYASINI ochadi — buyruqlarни ketma-ket
    qabul qiladi, WAKE_SESSION_SILENCE soniya jimlikда tinglashni bas qiladi. «Doda soat
    nechi» kabi bitta gapda aytilsa, darrov bajaradi. Farewell (xayr) -> SystemExit."""
    say("Tayyorman. Meni chaqirish uchun «Doda» deng.", "uz")
    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=1.0)
    except Exception as e:
        say("Mikrofonni ocholmadim. Mikrofon ruxsatini tekshiring.", "uz")
        _report_error("wake mikrofon", e)
        return
    print("🟢 Uyg'oq rejim: «Doda» deb chaqiring (jimlikda tinglamayapman).")
    while True:
        # Qisqa oynada tinglaymiz; JIMLIK bo'lsa -> WaitTimeoutError -> hech narsa qilmaymiz
        try:
            with sr.Microphone() as source:
                audio = _recognizer.listen(source, timeout=WAKE_LISTEN_TIMEOUT,
                                           phrase_time_limit=WAKE_PHRASE_LIMIT)
        except sr.WaitTimeoutError:
            continue
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            time.sleep(0.3)
            continue
        text = _transcribe_wake(audio)
        if not text:
            continue
        low = _norm(text)
        # 1) to'g'ridan-to'g'ri: wake so'zi matn ichida bormi
        hit = next((w for w in WAKE_WORDS if w in low), None)
        # 2) yumshoq (fuzzy): biror so'z «Doda»ga juda o'xshasa ham uyg'onamiz — STT
        #    «Doda»ni «doba/toda/doda.» kabi noto'g'ri yozsa ham ishlaydi.
        if not hit:
            for word in low.split():
                if difflib.get_close_matches(word, WAKE_WORDS, n=1, cutoff=0.72):
                    hit = word
                    break
        if not hit:
            continue                      # wake so'zi yo'q -> e'tibor bermaymiz
        print("🔔 Uyg'ondim:", text)
        after = low.split(hit, 1)[1].strip(" ,.!?-") if hit in low else ""
        if len(after) >= 2:               # «Doda soat nechi» -> darrov shu buyruqni bajaramiz
            _handle_locked(after)
        else:
            say_random(WAKE_REPLIES, "uz")   # shunchaki «Doda» -> «labbay»
        # «Doda» degach suhbat davom etadi: buyruqlarни ketma-ket qabul qiladi,
        # WAKE_SESSION_SILENCE soniya jim bo'lsangiz -> tinglashni bas qiladi.
        _wake_session()


def _text_loop():
    """Klaviatura orqali yozilган matnни qabul qiladi (ovoz oqими bilan parallel)."""
    while True:
        try:
            c = input("⌨️  Yozing (yoki «Doda» deb gapiring): ")
        except (EOFError, KeyboardInterrupt):
            raise SystemExit
        command = str(c).lower().strip()
        if not command:
            continue
        _handle_locked(command)


def greeting():
    """Ishga tushganda salomlashadi (ismni bilса, ishlatadi) va buyruq so'raydi."""
    name = _load_user_name()
    ism = (", " + name) if name else ""
    say_random([
        "Assalomu alaykum" + ism + "! Men Doda, ovozli yordamchingizman. Qalaysiz?",
        "Salom" + ism + "! Men Doda. Ishlaringiz qalay?",
        "Assalomu alaykum" + ism + "! Men Doda. Bugun kayfiyatingiz qanday?",
    ], "uz")
    say("Menga qanday buyruq berasiz? Gapiring yoki yozing.", "uz")


if __name__ == '__main__':
    _cleanup_temp_files()   # oldingi ishdan qolган vaqtinchalik fayllarni tozalaymiz
    # BUYRUQLAR.md ni har ishga tushganда avtomatik yangilaymiz
    try:
        import royxat_yarat as royxat_yarat
        royxat_yarat.yarat()
    except Exception as _e:
        print("BUYRUQLAR.md yangilanmadi:", _e)

    # Eslatmalarni fon rejimida kuzatadigan oqim (24/7 tayyor)
    threading.Thread(target=_reminder_loop, daemon=True).start()

    greeting()

    try:
        if INPUT_MODE == "wake":
            # IKKALASI birga: ovoz («Doda») — fon oqim; matn (klaviatura) — asosiy oqim.
            # Yozsangiz -> darrov javob. «Doda» desangiz -> tinglaydi, jim bo'lsangiz -> javob.
            def _wake_thread():
                while True:
                    try:
                        wake_loop()
                    except SystemExit:
                        return                          # ovozли xayr -> faqat ovoz oqими to'xtaydi
                    except Exception as e:
                        _report_error("wake-sikl", e)
                        time.sleep(0.5)
            threading.Thread(target=_wake_thread, daemon=True).start()
            _text_loop()                                # asosiy oqим: klaviatura
        else:
            while True:
                try:
                    c = listen()
                    command = str(c).lower().strip()
                    if not command:
                        continue  # jimlik yoki tanilmadi -> qayta tinglaymiz
                    handle_massage(command)
                except (KeyboardInterrupt, SystemExit):
                    raise                          # chiqishga ruxsat
                except Exception as e:
                    _report_error("desktop-sikl", e)   # qulamaymiz, davom etamiz
    except (KeyboardInterrupt, SystemExit):
        print("\nXayr! Dastur to'xtatildi.")
