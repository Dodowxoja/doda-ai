# -*- coding: utf-8 -*-
"""
DODA macOS tizim monitoringi — batareya, CPU, RAM, bufer (clipboard).

Buyruqlar asistent.py ichida EMAS — bu modul faqat MA'LUMOT beradi (o'lchaydi),
asistent.py esa uni chaqirib, ovoz/matn qilib javob qaytaradi.

Eslatma: ovoz balandligi va ekran yorqinligini BOSHQARISH allaqachon asistent.py da
(change_volume, brightness osascript) — bu modul asosan HOLATNI o'qish uchun.
"""
import re
import subprocess


def _run(cmd, timeout=8):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


def battery():
    """(foiz, holat_matni) — masalan ('97', 'batareyada, 14:36 qoldi')."""
    out = _run(["pmset", "-g", "batt"])
    mp = re.search(r"(\d+)%", out)
    pct = mp.group(1) if mp else None
    low = out.lower()
    if "ac power" in low and "charged" in low:
        holat = "to'lgan, quvvatda"
    elif "charging" in low and "discharging" not in low:
        holat = "quvvatlanmoqda"
    else:
        holat = "batareyada"
    mt = re.search(r"(\d+:\d\d) remaining", out)
    if mt and mt.group(1) != "0:00":
        holat += ", " + mt.group(1) + " qoldi"
    return pct, holat


def cpu_ram():
    """(cpu_band_foiz, ram_matni) — top orqali (bir chaqiriq)."""
    out = _run(["top", "-l", "1", "-n", "0"])
    cpu = None
    mc = re.search(r"CPU usage:\s*([\d.]+)% user,\s*([\d.]+)% sys", out)
    if mc:
        cpu = str(round(float(mc.group(1)) + float(mc.group(2))))
    ram = None
    mm = re.search(r"PhysMem:\s*([\d.]+[MG])\s+used.*?([\d.]+[MG])\s+unused", out)
    if mm:
        ram = "%s ishlatilgan, %s bo'sh" % (mm.group(1), mm.group(2))
    return cpu, ram


def report():
    """Birlashtirilgan holat: batareya + CPU + RAM — bitta o'qiladigan matn."""
    pct, holat = battery()
    cpu, ram = cpu_ram()
    q = []
    if pct:
        q.append("Batareya: " + pct + " foiz (" + holat + ")")
    if cpu:
        q.append("Protsessor yuklamasi: " + cpu + " foiz")
    if ram:
        q.append("Xotira (RAM): " + ram)
    return ". ".join(q) + "." if q else "Tizim holatini o'qib bo'lmadi."


def clipboard_text():
    """Almashtirish buferidagi (clipboard) matn."""
    return _run(["pbpaste"]).strip()


if __name__ == "__main__":
    print(report())
    print("Bufer:", (clipboard_text() or "(bo'sh)")[:100])
