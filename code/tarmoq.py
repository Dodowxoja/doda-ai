# -*- coding: utf-8 -*-
"""
DODA uy tarmog'i monitoringi — Wi-Fi/LAN'ga kim ulanganini kuzatadi.

`arp -a` orqali (root shart emas) yaqinda tarmoqda ko'ringan qurilmalarni oladi:
IP, MAC manzil. Tarix ~/.doda_network.json da saqlanadi (har qurilma uchun
birinchi/oxirgi ko'rilgan vaqt). Yangi qurilma paydo bo'lsa aniqlanadi.

Chuqurroq "kim qachon ulandi" tarixi routerning admin API'sini talab qiladi
(model-ga bog'liq) — bu esa LAN skaneri, hech qanday parol/karta ishlatmaydi.
"""
import os
import re
import json
import time
import subprocess
import datetime as dt

NET_FILE = os.path.expanduser("~/.doda_network.json")
HOME_FILE = os.path.expanduser("~/.doda_home_wifi")   # uy Wi-Fi nomi (SSID) shu yerda

# arp -a satri: "name (192.168.1.5) at a4:b1:c2:d3:e4:f5 on en0 ifscope [ethernet]"
_ARP_RE = re.compile(r"\(([\d.]+)\) at ([0-9a-fA-F:]+)")


def current_ssid():
    """Hozir ulangan Wi-Fi nomini (SSID) qaytaradi (yoki '')."""
    try:
        out = subprocess.run(["system_profiler", "SPAirPortDataType"],
                             capture_output=True, text=True, timeout=12).stdout
    except Exception:
        return ""
    # "Current Network Information:" dan keyingi qatorda "  SSID:" ko'rinishida
    lines = out.splitlines()
    for i, ln in enumerate(lines):
        if "Current Network Information:" in ln and i + 1 < len(lines):
            return lines[i + 1].strip().rstrip(":")
    return ""


def gateway_ip():
    """Router (default gateway) IP manzili."""
    try:
        out = subprocess.run(["route", "-n", "get", "default"],
                             capture_output=True, text=True, timeout=8).stdout
        m = re.search(r"gateway:\s*([\d.]+)", out)
        return m.group(1) if m else ""
    except Exception:
        return ""


def save_home(ssid=None):
    """Uy Wi-Fi(lar)ini eslab qoladi. BIR NECHTA nomni qo'llab-quvvatlaydi
    (masalan 'Doda' + 'Doda_5G' — bitta routerning 2.4G va 5G nomlari).
    ssid: bitta nom, vergul/qator bilan ajratilган nomlar, ro'yxat, yoki None (hozirgi)."""
    if ssid is None:
        ssid = current_ssid()
    if not ssid:
        return None
    if isinstance(ssid, (list, tuple)):
        names = [str(s).strip() for s in ssid if str(s).strip()]
    else:
        names = [s.strip() for s in re.split(r"[,\n]", str(ssid)) if s.strip()]
    if not names:
        return None
    with open(HOME_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(names))
    return names


def home_ssids():
    """Uy Wi-Fi nomlari ro'yxati (bir nechta bo'lishi mumkin)."""
    try:
        return [s.strip() for s in open(HOME_FILE, encoding="utf-8").read().splitlines() if s.strip()]
    except FileNotFoundError:
        return []


def home_ssid():
    """Birinchi uy Wi-Fi nomi (eski kod bilan moslik uchun)."""
    lst = home_ssids()
    return lst[0] if lst else ""


def is_home():
    """Hozir uy Wi-Fi'laridan birigami ulanganmiz? (True/False/None, joriy SSID)."""
    cur = current_ssid()
    homes = home_ssids()
    if not homes:
        return None, cur          # uy hali belgilanmagan
    return (cur in homes), cur


def scan():
    """Hozir tarmoqda ko'rinayotgan qurilmalar: [{'ip':.., 'mac':..}]."""
    try:
        # -n = raqamli (teskari DNS'siz, aks holda osilib qoladi)
        out = subprocess.run(["arp", "-a", "-n"], capture_output=True, text=True, timeout=10).stdout
    except Exception as e:
        print("arp xato:", e)
        return []
    seen = {}
    for line in out.splitlines():
        m = _ARP_RE.search(line)
        if not m:
            continue
        ip, mac = m.group(1), m.group(2).lower()
        okt = int(ip.split(".")[0])
        if (mac == "ff:ff:ff:ff:ff:ff" or mac.startswith(("1:0:5e", "01:00:5e", "33:33"))
                or ip.endswith(".255") or ip.startswith("169.254.") or 224 <= okt <= 239):
            continue  # broadcast / multicast / link-local'ni tashlab yuboramiz
        seen[mac] = ip
    return [{"ip": ip, "mac": mac} for mac, ip in seen.items()]


def _load():
    try:
        with open(NET_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save(data):
    try:
        with open(NET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("network.json yozib bo'lmadi:", e)


def update():
    """Skanerlab, tarixni yangilaydi. YANGI qurilmalar ro'yxatini qaytaradi ([{ip,mac,nom}]).

    MUHIM: tarix FAQAT uy Wi-Fi'sida yozib boriladi. Boshqa tarmoqда (ishxona va h.k.)
    umuman yozilmaydi — foydalanuvchi faqat uy tarixini xohlaydi."""
    home_ok = is_home()[0]
    if home_ok is not True:
        return []                      # uy Wi-Fi emas -> tarixga yozmaymiz
    now = time.time()
    hist = _load()
    yangi = []
    for dev in scan():
        mac = dev["mac"]
        if mac in hist:
            hist[mac]["last"] = now
            hist[mac]["ip"] = dev["ip"]
        else:
            hist[mac] = {"ip": dev["ip"], "first": now, "last": now, "nom": ""}
            yangi.append({"ip": dev["ip"], "mac": mac, "nom": ""})
    _save(hist)
    return yangi


def _vaqt(ts):
    return dt.datetime.fromtimestamp(ts).strftime("%d-%b %H:%M")


def rename(mac, nom):
    """Qurilmaga tanish nom beradi (masalan 'a4:..' -> 'Onamning telefoni')."""
    hist = _load()
    mac = mac.lower()
    if mac in hist:
        hist[mac]["nom"] = nom
        _save(hist)
        return True
    return False


def summary(active_within=600):
    """O'qiladigan ro'yxat: uy tarmog'i holati + hozir ulangan + tarix."""
    now = time.time()
    hist = _load()
    gw = gateway_ip()
    # Sarlavha: uy Wi-Fi holati
    lines = []
    homes = home_ssids()
    home = " / ".join(homes)
    cur = current_ssid()
    if homes:
        if cur in homes:
            lines.append("🏠 Uy Wi-Fi'sida: «%s» ✅" % cur)
        elif cur:
            lines.append("📍 Boshqa tarmoqda: «%s» (uy: «%s») — tarix yozilmaydi" % (cur, home))
        else:
            lines.append("⚠️ Wi-Fi aniqlanmadi (uy: «%s»)" % home)
    elif cur:
        lines.append("📶 Tarmoq: «%s» (uy sifatida saqlash: «wifi'ni uy deb saqla»)" % cur)
    lines.append("")

    if not hist:
        lines.append("Hali qurilmalar skanerlanmagan. «kim ulandi» deng.")
        return "\n".join(lines)

    active, past = [], []
    for mac, d in sorted(hist.items(), key=lambda x: -x[1]["last"]):
        nom = d.get("nom") or d["ip"]
        belgi = " 🛜(router)" if d["ip"] == gw else ""
        qator = "• %s  [%s]%s  — oxirgi: %s" % (nom, mac, belgi, _vaqt(d["last"]))
        if now - d["last"] <= active_within:
            active.append(qator)
        else:
            past.append(qator)
    lines.append("🟢 Hozir ulangan (%d ta):" % len(active))
    lines += active or ["  (yo'q)"]
    if past:
        lines += ["", "⚪️ Ilgari ko'rilgan (%d ta):" % len(past)] + past[:20]
    return "\n".join(lines)


if __name__ == "__main__":
    print("Yangi qurilmalar:", update())
    print()
    print(summary())
