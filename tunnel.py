# -*- coding: utf-8 -*-
"""
DODA tunnel — dashboard'ni internetга HTTPS bilan ochadi (Telegram Mini App uchun).

cloudflared quick tunnel'ni ishga tushiradi, public URL'ni ushlab, ~/.doda_tunnel_url
fayliga yozadi (bot shu fayldan o'qib, Mini App tugmasini beradi). Tunnel uzilsa,
launchd (com.doda.tunnel) uni qayta ishga tushiradi — har safar yangi URL yoziladi.

Ishga tushirish: python3 tunnel.py
"""
import os
import re
import sys
import signal
import subprocess

URL_FILE = os.path.expanduser("~/.doda_tunnel_url")
# DOIMIY (named) tunnel sozlamasi. Ikki qatorli fayl:
#   1-qator: tunnel nomi (yoki UUID)
#   2-qator: doimiy public URL, masalan https://doda.sizningdomen.com
# Fayl bo'lsa -> URL HECH QACHON o'zgarmaydi (Mini App uchun ideal).
# Sozlash: pastdagi TUNNEL_SETUP.md ga qarang.
NAMED_FILE = os.path.expanduser("~/.doda_named_tunnel")
LOCAL = "http://localhost:8765"
_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def _named_config():
    """Doimiy tunnel sozlangan bo'lsa (nom, url) qaytaradi, aks holda None."""
    try:
        lines = [l.strip() for l in open(NAMED_FILE, encoding="utf-8").read().splitlines() if l.strip()]
        if len(lines) >= 2 and lines[1].startswith("https://"):
            return lines[0], lines[1]
    except FileNotFoundError:
        pass
    return None


def main():
    # eski URL faylini tozalaymiz (yangi URL kelguncha bot eski URL bermasin)
    try:
        os.remove(URL_FILE)
    except FileNotFoundError:
        pass

    named = _named_config()
    if named:
        # DOIMIY tunnel: URL o'zgarmaydi. Nomни ishga tushiramiz, URLни darrov yozamiz.
        name, url = named
        with open(URL_FILE, "w") as f:
            f.write(url)
        os.chmod(URL_FILE, 0o600)
        print("✅ Doimiy tunnel URL (o'zgarmaydi):", url)
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "run", name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        try:
            for _ in proc.stdout:
                pass                       # jurnalни o'qib turamiz (tirik qolish uchun)
        finally:
            pass
        # cloudflared chiqib ketsa -> launchd qayta ishga tushiradi (URL o'zgarmaydi)
        try:
            proc.terminate()
        except Exception:
            pass
        return

    # QUICK tunnel (vaqtinchalik, URL har safar o'zgaradi)
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", LOCAL],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    def _cleanup(*_):
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            os.remove(URL_FILE)
        except FileNotFoundError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    url_written = False
    for line in proc.stdout:
        if not url_written:
            m = _URL_RE.search(line)
            if m:
                url = m.group(0)
                with open(URL_FILE, "w") as f:
                    f.write(url)
                os.chmod(URL_FILE, 0o600)
                print("✅ Tunnel URL:", url)
                url_written = True
    # cloudflared chiqib ketsa -> launchd qayta ishga tushiradi
    _cleanup()


if __name__ == "__main__":
    main()
