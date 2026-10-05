# -*- coding: utf-8 -*-
"""DODA uyg'otkich — belgilangan vaqtda ishga tushib egasini UYG'OTADI.

launchd (com.doda.alarm.plist) shu skriptni chaqiradi. Uch kanal:
  1) Telefonga Telegram push (Mac uxlab qolsa ham telefon bildirishnomasi uyg'otadi)
  2) Baland ovozli signal (afplay, ovoz balandligini 90% ga ko'taradi)
  3) macOS «say» bilan gapiradi

Ishlatish:  python3 uygotkich.py "Turish vaqti! Soat 7:00"
"""
import os
import sys
import time
import subprocess
import urllib.parse
import urllib.request

TOKEN_FILE = os.path.expanduser("~/.doda_bot_token")
USERS_FILE = os.path.expanduser("~/.doda_bot_users")
ALARM_SOUND = "/System/Library/Sounds/Sosumi.aiff"   # baland, tiniq signal


def _token():
    try:
        return open(TOKEN_FILE).read().strip()
    except Exception:
        return ""


def _owner_ids():
    try:
        return [x for x in open(USERS_FILE).read().split() if x.strip().isdigit()]
    except Exception:
        return []


def telegram_push(text):
    tok = _token()
    if not tok:
        return
    for cid in _owner_ids():
        try:
            data = urllib.parse.urlencode({"chat_id": cid, "text": text}).encode()
            urllib.request.urlopen(
                "https://api.telegram.org/bot%s/sendMessage" % tok, data=data, timeout=10)
        except Exception as e:
            print("telegram xato:", e)


def loud_alarm(note, seconds=45):
    """Ovozni ko'tarib, signalni ~45 soniya davomida takror chaladi + gapiradi."""
    try:
        subprocess.run(["osascript", "-e", "set volume output volume 90"], capture_output=True)
    except Exception:
        pass
    end = time.time() + seconds
    said = 0
    while time.time() < end:
        if os.path.exists(ALARM_SOUND):
            subprocess.run(["afplay", ALARM_SOUND], capture_output=True)
        else:
            subprocess.run(["osascript", "-e", "beep 3"], capture_output=True)
        if said < 5:            # har aylanada bir marta gapiradi (macOS built-in ovoz)
            subprocess.run(["say", "-v", "Milena", "Пора вставать! " + note],
                           capture_output=True)   # o'zbekcha ovoz yo'q -> ruscha
            said += 1
        time.sleep(0.3)


def main():
    note = sys.argv[1] if len(sys.argv) > 1 else "Turish vaqti!"
    telegram_push("⏰⏰⏰ UYG'ONING!\n" + note)
    loud_alarm(note)


if __name__ == "__main__":
    main()
