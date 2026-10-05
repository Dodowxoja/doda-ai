# -*- coding: utf-8 -*-
"""
DODA Web Dashboard — brauzerdan boshqaruv paneli (Mac'da lokal server).

Tashqi kutubxona SHART EMAS — Python'ning o'rnatilgan http.server bilan ishlaydi.
LAN'da ochiladi (telefon'dan ham kirasiz): http://<mac-ip>:8765/?t=<token>

Xavfsizlik: maxfiy token (~/.doda_web_token). Tokensiz hech kim kira olmaydi.
API'lar asistent.py / mac_system.py / tarmoq.py / vision.py ni chaqiradi.

Ishga tushirish:  python3 web_dashboard.py
"""
import os
import re
import sys
import hmac
import json
import time
import hashlib
import secrets
import threading
import http.server
import urllib.parse
import socketserver

import code.asistent as asistent
import code.mac_system as mac_system
import code.tarmoq as tarmoq
import code.vision as vision
import code.ruxsatlar as ruxsatlar   # macOS ruxsatlarini tekshirish
import code.boshqaruv as boshqaruv   # uzoqdan tap-to-control (sichqoncha/klaviatura)

PORT = 8765
_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(_DIR, "dashboard.html")
TOKEN_FILE = os.path.expanduser("~/.doda_web_token")
BOT_TOKEN_FILE = os.path.expanduser("~/.doda_bot_token")
USERS_FILE = os.path.expanduser("~/.doda_bot_users")
_lock = threading.Lock()


def _bot_token():
    try:
        return open(BOT_TOKEN_FILE).read().strip()
    except FileNotFoundError:
        return ""


def _authorized_ids():
    try:
        return set(x for x in open(USERS_FILE).read().split() if x.strip().isdigit())
    except FileNotFoundError:
        return set()


def verify_telegram(init_data):
    """Telegram Mini App initData imzosini bot tokeni bilan tekshiradi.
    To'g'ri VA foydalanuvchi avtorizatsiyalangan bo'lsa -> user_id (str), aks holda None.
    (Telegram rasmiy algoritmi: HMAC-SHA256, secret = HMAC('WebAppData', bot_token).)"""
    bot_token = _bot_token()
    if not bot_token or not init_data:
        return None
    try:
        pairs = urllib.parse.parse_qsl(init_data, keep_blank_values=True)
        data = dict(pairs)
        their_hash = data.pop("hash", None)
        if not their_hash:
            return None
        check = "\n".join("%s=%s" % (k, data[k]) for k in sorted(data))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, their_hash):
            return None
        # auth_date juda eski bo'lmasin (24 soat)
        if time.time() - int(data.get("auth_date", "0")) > 86400:
            return None
        user = json.loads(data.get("user", "{}"))
        uid = str(user.get("id", ""))
        if uid and uid in _authorized_ids():
            return uid
        return None
    except Exception:
        return None


def _get_token():
    """Maxfiy tokenni o'qiydi (yo'q bo'lsa yaratadi)."""
    try:
        t = open(TOKEN_FILE).read().strip()
        if t:
            return t
    except FileNotFoundError:
        pass
    t = secrets.token_urlsafe(16)
    with open(TOKEN_FILE, "w") as f:
        f.write(t)
    os.chmod(TOKEN_FILE, 0o600)
    return t


TOKEN = _get_token()
ERRORS_LOG = os.path.expanduser("logs/.doda_errors.log")


def _api_status():
    pct, holat = mac_system.battery()
    cpu, ram = mac_system.cpu_ram()
    hb = os.path.expanduser("~/.doda_bot_heartbeat")
    try:
        bot_alive = (time.time() - int(open(hb).read().strip())) < 60
    except Exception:
        bot_alive = False
    return {
        "bot": bot_alive,
        "battery_pct": pct, "battery_state": holat,
        "cpu": cpu, "ram": ram,
        "clipboard": (mac_system.clipboard_text() or "")[:300],
    }


def _api_network():
    tarmoq.update()
    return {"summary": tarmoq.summary()}


def _api_logs():
    try:
        with open(ERRORS_LOG, encoding="utf-8", errors="replace") as f:
            return {"logs": f.read()[-4000:]}
    except FileNotFoundError:
        return {"logs": ""}


def _api_command(text):
    with _lock:
        reply = asistent.process_text(text)
    return {"reply": reply}


def _api_permissions():
    """macOS ruxsatlari holati (shu dashboard jarayoni uchun)."""
    res = ruxsatlar.check_all()
    titles = {"screen": "Ekranni yozib olish", "accessibility": "Foydalanish imkoniyati",
              "fulldisk": "To'liq disk ruxsati", "camera": "Kamera"}
    paths = {"screen": "Privacy & Security → Screen Recording",
             "accessibility": "Privacy & Security → Accessibility",
             "fulldisk": "Privacy & Security → Full Disk Access",
             "camera": "Privacy & Security → Camera"}
    items = [{"key": k, "title": titles[k], "path": paths[k], "ok": res[k]} for k in res]
    return {"items": items, "python": ruxsatlar.python_path(),
            "all_ok": all(v is True for v in res.values())}


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # jim (konsolni ifloslamaymiz)

    def _auth_ok(self, qs):
        # 1) Maxfiy token (?t= yoki cookie) — LAN/brauzer uchun.
        #    hmac.compare_digest — doimiy vaqtli solishtiruv (timing-attack himoyasi).
        if hmac.compare_digest(qs.get("t", [""])[0] or "", TOKEN):
            return True
        cookie = self.headers.get("Cookie", "")
        m = re.search(r"doda_token=([^;\s]+)", cookie)
        if m and hmac.compare_digest(m.group(1), TOKEN):
            return True
        # 2) Telegram Mini App initData imzosi (header yoki query) — faqat siz kirasiz
        init = self.headers.get("X-Telegram-Init", "") or (qs.get("tg", [""])[0])
        if init and verify_telegram(init):
            return True
        return False

    def _send(self, code, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if extra:
            for k, v in extra.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_HEAD(self):
        # Sog'liq tekshiruvi (bot _url_alive) — tanasiz 200 (maxfiy ma'lumot yo'q).
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # HTML sahifa (/) HIMOYASIZ ochiladi — u bo'sh UI, maxfiy ma'lumot yo'q.
        # Telegram Mini App uni ochadi; JS keyin initData'ni API'larga header'da yuboradi.
        # BARCHA /api/* himoyalangan (token yoki Telegram imzosi).
        if path == "/" or path == "/index.html":
            try:
                with open(HTML_FILE, "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(500, "dashboard.html topilmadi", "text/plain; charset=utf-8")
            return

        # Avatar (3D point-cloud yuz) — maxfiy ma'lumot yo'q, animatsiya faqat
        if path == "/avatar.html":
            try:
                with open(os.path.join(_DIR, "avatar.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                self._send(404, "avatar.html topilmadi", "text/plain; charset=utf-8")
            return
        # Avatar manba rasmi (zarrachalar shundan o'qiladi)
        if path == "/avatar_face.png":
            try:
                with open(os.path.join(_DIR, "image", "avatar_ai_face.png"), "rb") as f:
                    self._send(200, f.read(), "image/png")
            except FileNotFoundError:
                self._send(404, "rasm topilmadi", "text/plain; charset=utf-8")
            return

        # Sog'liq tekshiruvi (monitoring/watchdog) — AUTH'SIZ, maxfiy ma'lumot yo'q.
        if path == "/health":
            hb = os.path.expanduser("~/.doda_bot_heartbeat")
            try:
                bot_alive = (time.time() - int(open(hb).read().strip())) < 60
            except Exception:
                bot_alive = False
            self._send(200, json.dumps({"ok": True, "service": "doda-dashboard",
                                        "bot": bot_alive}), "application/json")
            return

        if not self._auth_ok(qs):
            self._send(403, "Ruxsat yo'q.", "text/plain; charset=utf-8")
            return

        # Token to'g'ri -> cookie o'rnatamiz (LAN brauzer uchun; keyin ?t= shart emas)
        # HttpOnly — JS cookie'ni o'qiy olmaydi (XSS'да o'g'irlanmaydi; UI faqat ?t= ishlatadi).
        # SameSite=Strict — cookie boshqa saytdan yuborilgan so'rovga QO'SHILMAYDI (CSRF himoyasi).
        set_cookie = {"Set-Cookie":
                      "doda_token=%s; Path=/; Max-Age=2592000; HttpOnly; SameSite=Strict" % TOKEN}

        if False:
            pass
        elif path == "/api/status":
            self._send(200, json.dumps(_api_status(), ensure_ascii=False), extra=set_cookie)
        elif path == "/api/network":
            self._send(200, json.dumps(_api_network(), ensure_ascii=False), extra=set_cookie)
        elif path == "/api/logs":
            self._send(200, json.dumps(_api_logs(), ensure_ascii=False), extra=set_cookie)
        elif path == "/api/permissions":
            self._send(200, json.dumps(_api_permissions(), ensure_ascii=False), extra=set_cookie)
        elif path == "/api/screenshot":
            p = vision.capture_screen()
            if p and os.path.exists(p):
                with open(p, "rb") as f:
                    img = f.read()
                os.remove(p)
                self._send(200, img, "image/png", set_cookie)
            else:
                self._send(500, "Ekran olinmadi (Screen Recording ruxsati?)",
                           "text/plain; charset=utf-8")
        elif path == "/api/camera":
            p = vision.capture_camera()
            if p and os.path.exists(p):
                with open(p, "rb") as f:
                    img = f.read()
                os.remove(p)
                self._send(200, img, "image/jpeg", set_cookie)
            else:
                self._send(500, "Kamera olinmadi (Camera ruxsati?)",
                           "text/plain; charset=utf-8")
        elif path == "/api/tts":
            # Matnни ovozга aylantirib mp3 qaytaramiz (brauzer chaladi -> telefonда ovoz)
            text = (qs.get("text", [""])[0] or "").strip()[:600]
            lang = (qs.get("lang", [""])[0] or "").strip()
            if not lang:   # til berilmasa: kirillcha bo'lsa ru, aks holda uz
                lang = "ru" if any("Ѐ" <= c <= "ӿ" for c in text) else "uz"
            audio = asistent.tts_bytes(text, lang) if text else b""
            if audio:
                self._send(200, audio, "audio/mpeg", set_cookie)
            else:
                self._send(500, "Ovoz yaratilmadi", "text/plain; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        if not self._auth_ok(qs):
            self._send(403, "Ruxsat yo'q.", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {}
        if parsed.path == "/api/command":
            text = (body.get("text") or "").strip()
            if not text:
                self._send(400, json.dumps({"reply": "Bo'sh buyruq."}))
                return
            self._send(200, json.dumps(_api_command(text), ensure_ascii=False))
        # ----- Uzoqdan tap-to-control -----
        elif parsed.path == "/api/click":
            try:
                boshqaruv.click_fraction(
                    float(body.get("xf", 0)), float(body.get("yf", 0)),
                    button=body.get("button", "left"), double=bool(body.get("double")))
                self._send(200, json.dumps({"ok": True}))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "err": str(e)}))
        elif parsed.path == "/api/type":
            try:
                boshqaruv.type_text(body.get("text", ""))
                self._send(200, json.dumps({"ok": True}))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "err": str(e)}))
        elif parsed.path == "/api/key":
            try:
                ok = boshqaruv.press_key(body.get("key", ""))
                self._send(200, json.dumps({"ok": bool(ok)}))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "err": str(e)}))
        elif parsed.path == "/api/scroll":
            try:
                boshqaruv.scroll(body.get("dir", "down"), int(body.get("amount", 5)))
                self._send(200, json.dumps({"ok": True}))
            except Exception as e:
                self._send(500, json.dumps({"ok": False, "err": str(e)}))
        else:
            self._send(404, "not found", "text/plain")


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # Brauzer ulanishни o'rtada uzsa (BrokenPipe/ConnectionReset) — bu NORMAL holat,
        # traceback bilan log'ni ifloslamaymiz. Boshqa xatolar odatdagidek chiqadi.
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def main():
    ip = "0.0.0.0"
    srv = Server((ip, PORT), Handler)
    try:
        local_ip = __import__("socket").gethostbyname(__import__("socket").gethostname())
    except Exception:
        local_ip = "localhost"
    print("✅ DODA dashboard ishga tushdi.")
    print("   Bu Mac'da:   http://localhost:%d/?t=%s" % (PORT, TOKEN))
    print("   Tarmoqdan:   http://%s:%d/?t=%s" % (local_ip, PORT, TOKEN))
    print("   (token maxfiy — havolani boshqaga bermang)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard to'xtatildi.")
        srv.shutdown()


if __name__ == "__main__":
    main()
