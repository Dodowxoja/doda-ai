# -*- coding: utf-8 -*-
"""
DODA menyu-bar app — Mac'ning yuqori panelidagi 🎙️ ikonka.

Holatni ko'rsatadi (batareya, CPU, bot) va tez tugmalar beradi:
  - Ekran rasmini olish (Preview'da ochadi)
  - Dashboard'ni brauzerda ochish
  - Bot / Dashboard'ni qayta ishga tushirish
  - Tarmoq holati, tizim holati
  - Buyruq yozib yuborish (DODA bajaradi)

Talab: rumps (pip install rumps). Ishga tushirish: python3 menubar.py
"""
import os
import time
import threading
import subprocess
import webbrowser

import rumps

import asistent
import mac_system
import tarmoq
import vision

HEARTBEAT = os.path.expanduser("~/.doda_bot_heartbeat")
TOKEN_FILE = os.path.expanduser("~/.doda_web_token")
UID = os.getuid()


def _bot_alive():
    try:
        return (time.time() - int(open(HEARTBEAT).read().strip())) < 60
    except Exception:
        return False


def _local_ip():
    try:
        import socket
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "localhost"


def _kickstart(service):
    subprocess.run(["launchctl", "kickstart", "-k", "gui/%d/%s" % (UID, service)],
                   capture_output=True)


def _notify(title, subtitle, message):
    """macOS bildirishnoma — XAVFSIZ. Skript .app bundle sifatida qadoqlanmaganда
    rumps.notification 'Info.plist/CFBundleIdentifier' RuntimeError beradi (log'ni
    ifloslaydi). Shu sabab try/except — bildirishnoma ko'rinmasa ham amal bajariladi."""
    try:
        rumps.notification(title, subtitle, message)
    except Exception:
        print("[bildirishnoma] %s: %s" % (title, message))


class DodaApp(rumps.App):
    def __init__(self):
        super().__init__("🎙️ DODA", quit_button=None)
        self.menu = [
            "Holat yangilanmoqda…",
            None,
            rumps.MenuItem("📷 Ekran rasmini olish", callback=self.screenshot),
            rumps.MenuItem("🌐 Dashboard'ni ochish", callback=self.open_dashboard),
            rumps.MenuItem("⌨️ Buyruq yuborish…", callback=self.send_command),
            None,
            rumps.MenuItem("📡 Tarmoq — kim ulangan", callback=self.network),
            rumps.MenuItem("💻 Tizim holati", callback=self.sysinfo),
            None,
            rumps.MenuItem("🔄 Botni qayta ishga tushir", callback=self.restart_bot),
            rumps.MenuItem("🔄 Dashboard'ni qayta ishga tushir", callback=self.restart_dash),
            None,
            rumps.MenuItem("Chiqish", callback=rumps.quit_application),
        ]
        # Har 15 soniyada holatni yangilaydi
        self._timer = rumps.Timer(self.refresh, 15)
        self._timer.start()
        self.refresh(None)

    def refresh(self, _):
        def work():
            pct, _st = mac_system.battery()
            cpu, _ram = mac_system.cpu_ram()
            bot = "🟢" if _bot_alive() else "🔴"
            line = "%s Bot  ·  🔋 %s%%  ·  💻 %s%%" % (
                bot, pct or "?", cpu or "?")
            # Menyu birinchi bandini yangilaymiz (asosiy thread'da)
            try:
                self.menu["Holat yangilanmoqda…"].title = line
            except KeyError:
                # allaqachon yangilanган -> birinchi bandni topamiz
                first = next(iter(self.menu.values()))
                first.title = line
        threading.Thread(target=work, daemon=True).start()

    def screenshot(self, _):
        def work():
            p = vision.capture_screen()
            if p and os.path.exists(p):
                subprocess.run(["open", p])   # Preview'da ochadi
            else:
                _notify("DODA", "Ekran", "Olinmadi — Screen Recording ruxsati?")
        threading.Thread(target=work, daemon=True).start()

    def open_dashboard(self, _):
        try:
            token = open(TOKEN_FILE).read().strip()
        except FileNotFoundError:
            token = ""
        webbrowser.open("http://%s:8765/?t=%s" % (_local_ip(), token))

    def send_command(self, _):
        resp = rumps.Window(
            message="DODA'ga buyruq yozing:",
            title="Buyruq", default_text="", ok="Yubor", cancel="Bekor",
            dimensions=(300, 24)).run()
        if resp.clicked and resp.text.strip():
            def work():
                reply = asistent.process_text(resp.text.strip())
                _notify("DODA", resp.text.strip(), reply or "bajarildi")
            threading.Thread(target=work, daemon=True).start()

    def network(self, _):
        def work():
            tarmoq.update()
            s = tarmoq.summary()
            # birinchi 3 qatorни bildirishnomada ko'rsatamiz
            head = "\n".join(s.splitlines()[:4])
            _notify("DODA — tarmoq", "", head)
        threading.Thread(target=work, daemon=True).start()

    def sysinfo(self, _):
        def work():
            _notify("DODA — tizim", "", mac_system.report())
        threading.Thread(target=work, daemon=True).start()

    def restart_bot(self, _):
        _kickstart("com.doda.bot")
        _notify("DODA", "Bot", "Qayta ishga tushirildi ✅")

    def restart_dash(self, _):
        _kickstart("com.doda.dashboard")
        _notify("DODA", "Dashboard", "Qayta ishga tushirildi ✅")


if __name__ == "__main__":
    DodaApp().run()
