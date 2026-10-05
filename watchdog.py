# -*- coding: utf-8 -*-
"""
DODA watchdog — botdan MUSTAQIL kuzatuvchi.

Muammo: bot o'zi yiqilsa, o'zi orqali "yiqildim" deb ayta olmaydi.
Yechim: bu skript alohida (launchd orqali har 2 daqiqada) ishlaydi va:
  1) Bot yozib turadigan "heartbeat" faylini tekshiradi (~/.doda_bot_heartbeat).
  2) Heartbeat eski (>150s) yoki yo'q bo'lsa -> bot o'lган/qotган ->
       - launchd orqali qayta ishga tushiradi (kickstart),
       - Telegram orqali TO'G'RIDAN (urllib) egasiga xabar yuboradi,
       - macOS bildirishnomasi ko'rsatadi.
  3) Ogohlantirishlarni cheklaydi (30 daqiqada bir marta) — spam bo'lmasin.

Ishga tushirish (launchd): com.doda.watchdog.plist har 120s da chaqiradi.
"""
import os
import time
import subprocess
import urllib.parse
import urllib.request

HEARTBEAT_FILE = os.path.expanduser("~/.doda_bot_heartbeat")
TOKEN_FILE = os.path.expanduser("~/.doda_bot_token")
USERS_FILE = os.path.expanduser("~/.doda_bot_users")
ALERT_STAMP = os.path.expanduser("~/.doda_watchdog_alert")

STALE_SECONDS = 150        # heartbeat shundan eski bo'lsa -> bot o'lган
ALERT_COOLDOWN = 1800      # ogohlantirishlar orasidagi minimal vaqt (30 daqiqa)
SERVICE = "com.doda.bot"


def _token():
    tok = os.environ.get("TELEGRAM_BOT_TOKEN")
    if tok:
        return tok.strip()
    try:
        return open(TOKEN_FILE).read().strip()
    except FileNotFoundError:
        return None


def _users():
    try:
        return [int(x) for x in open(USERS_FILE).read().split() if x.strip().isdigit()]
    except FileNotFoundError:
        return []


def heartbeat_age():
    """Heartbeat necha soniya oldin yozilgan (yo'q bo'lsa juda katta son)."""
    try:
        ts = int(open(HEARTBEAT_FILE).read().strip())
        return time.time() - ts
    except (FileNotFoundError, ValueError):
        return 10 ** 9


def _recently_alerted():
    try:
        return (time.time() - float(open(ALERT_STAMP).read().strip())) < ALERT_COOLDOWN
    except (FileNotFoundError, ValueError):
        return False


def _mark_alerted():
    try:
        open(ALERT_STAMP, "w").write(str(time.time()))
    except Exception:
        pass


def telegram_alert(text):
    """Botdan MUSTAQIL ravishda (urllib) egasiga xabar yuboradi."""
    tok = _token()
    if not tok:
        return
    for uid in _users():
        try:
            data = urllib.parse.urlencode({"chat_id": uid, "text": text}).encode()
            urllib.request.urlopen(
                "https://api.telegram.org/bot%s/sendMessage" % tok, data=data, timeout=10)
        except Exception:
            pass


def macos_notify(text):
    try:
        subprocess.run(["osascript", "-e",
                        'display notification "%s" with title "DODA watchdog"' % text],
                       timeout=10)
    except Exception:
        pass


def restart_bot():
    uid = os.getuid()
    try:
        subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (uid, SERVICE)],
                       timeout=20)
        return True
    except Exception:
        return False


def main():
    age = heartbeat_age()
    if age <= STALE_SECONDS:
        return  # bot sog'lom
    # Bot o'lган/qotган
    restarted = restart_bot()
    if _recently_alerted():
        return  # yaqinda ogohlantirilgan -> spam qilmaymiz
    _mark_alerted()
    holat = "qayta ishga tushirdim ✅" if restarted else "qayta ishga tushira olmadim ⚠️"
    msg = ("⚠️ DODA bot javob bermayapti (heartbeat %d soniya eski). %s"
           % (int(age), holat))
    telegram_alert(msg)
    macos_notify("Bot javob bermadi — " + holat)


if __name__ == "__main__":
    main()
