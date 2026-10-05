# -*- coding: utf-8 -*-
"""DODA — macOS ruxsatlarini tekshirish va foydalanuvchiga aniq yo'l ko'rsatish.

Uch asosiy ruxsat (foydalanuvchi so'ragan) + kamera:
  - Screen Recording  (ekran suratini olish)
  - Accessibility     (klaviatura/sichqoncha, oynalarni boshqarish)
  - Full Disk Access  (himoyalangan fayllarni o'qish)
  - Camera            (kamera surati/videosi)

Har bir tekshiruv Apple'ning rasmiy preflight API'sidan foydalanadi
(pyobjc: Quartz / ApplicationServices). Agar u mavjud bo'lmasa yoki
xato bersa — shell fallback ishlaydi. HECH QACHON osilib qolmaydi:
har bir ichki chaqiruv timeout bilan o'ralgan yoki prompt-siz.

MUHIM: ruxsat CHAQIRUVCHI JARAYONGA bog'liq. launchd bot python'i
(sys.executable) ekan tekshirsa, aynan o'sha python uchun holatni
qaytaradi — bu bizga kerak (ruxsatlar har jarayon uchun alohida
beriladi, memory'dagi "per-process gotcha").
"""
import os
import sys
import subprocess

# System Settings > Privacy & Security ichidagi to'g'ridan-to'g'ri havolalar
_PANES = {
    "screen":       "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
    "accessibility": "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
    "fulldisk":     "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles",
    "camera":       "x-apple.systempreferences:com.apple.preference.security?Privacy_Camera",
}

# Foydalanuvchiga ko'rsatiladigan o'zbekcha yo'llar
_PATHS = {
    "screen":       "System Settings → Privacy & Security → Screen Recording",
    "accessibility": "System Settings → Privacy & Security → Accessibility",
    "fulldisk":     "System Settings → Privacy & Security → Full Disk Access",
    "camera":       "System Settings → Privacy & Security → Camera",
}

_TITLES = {
    "screen":       "Ekranni yozib olish (Screen Recording)",
    "accessibility": "Foydalanish imkoniyati (Accessibility)",
    "fulldisk":     "To'liq disk ruxsati (Full Disk Access)",
    "camera":       "Kamera (Camera)",
}


def python_path():
    """Ruxsat berilishi kerak bo'lgan aynan shu python ijro fayli."""
    return sys.executable or "/usr/bin/python3"


# ---------- Screen Recording ----------
def check_screen_recording():
    """True = ruxsat bor, False = yo'q, None = aniqlab bo'lmadi."""
    # 1) Apple preflight API (prompt chiqarmaydi)
    try:
        import Quartz
        if hasattr(Quartz, "CGPreflightScreenCaptureAccess"):
            return bool(Quartz.CGPreflightScreenCaptureAccess())
    except Exception:
        pass
    # 2) Fallback: screencapture'ni jimgina sinab ko'ramiz
    try:
        import tempfile
        f = os.path.join(tempfile.gettempdir(), ".doda_srtest.png")
        r = subprocess.run(["screencapture", "-x", "-t", "png", f],
                           capture_output=True, timeout=8)
        ok = r.returncode == 0 and os.path.exists(f) and os.path.getsize(f) > 1000
        try:
            os.remove(f)
        except OSError:
            pass
        return ok if r.returncode == 0 else None
    except Exception:
        return None


# ---------- Accessibility ----------
def check_accessibility():
    """True = ruxsat bor, False = yo'q, None = aniqlab bo'lmadi."""
    # 1) Apple preflight API (prompt chiqarmaydi — options=None)
    try:
        import ApplicationServices as A
        if hasattr(A, "AXIsProcessTrustedWithOptions"):
            return bool(A.AXIsProcessTrustedWithOptions(None))
        if hasattr(A, "AXIsProcessTrusted"):
            return bool(A.AXIsProcessTrusted())
    except Exception:
        pass
    # 2) Fallback: System Events'ga zararsiz so'rov; "assistive access" xatosi = ruxsat yo'q
    try:
        r = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to return name of first process'],
            capture_output=True, text=True, timeout=8)
        err = (r.stderr or "").lower()
        if "assistive" in err or "not allowed" in err or "1002" in err:
            return False
        return r.returncode == 0
    except Exception:
        return None


# ---------- Full Disk Access ----------
def check_full_disk_access():
    """True = ruxsat bor, False = yo'q, None = aniqlab bo'lmadi.

    TCC bilan himoyalangan yo'lni o'qishga urinamiz. Ruxsat bo'lmasa
    macOS PermissionError beradi; bo'lsa o'qiladi.
    """
    # Bir nechta himoyalangan manzil — biri o'qilsa, FDA bor
    candidates = [
        os.path.expanduser("~/Library/Application Support/com.apple.TCC/TCC.db"),
        os.path.expanduser("~/Library/Messages/chat.db"),
        os.path.expanduser("~/Library/Mail"),
        os.path.expanduser("~/Library/Safari/History.db"),
    ]
    saw_target = False
    for p in candidates:
        if not os.path.exists(p):
            continue
        saw_target = True
        try:
            if os.path.isdir(p):
                os.listdir(p)
            else:
                with open(p, "rb") as fh:
                    fh.read(16)
            return True          # o'qildi -> FDA bor
        except PermissionError:
            return False         # aniq rad etildi -> FDA yo'q
        except Exception:
            continue
    return None if not saw_target else False


# ---------- Camera ----------
def check_camera():
    """True/False/None. AVFoundation bo'lsa aniq holat; bo'lmasa None (probe qilmaymiz)."""
    try:
        import AVFoundation  # pyobjc-framework-AVFoundation (o'rnatilmagan bo'lishi mumkin)
        # 0=notDetermined 1=restricted 2=denied 3=authorized
        st = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
            AVFoundation.AVMediaTypeVideo)
        if st == 3:
            return True
        if st in (1, 2):
            return False
        return None
    except Exception:
        return None  # kamerani probe qilib chirog'ini yoqmaymiz


# ---------- Umumiy hisobot ----------
_CHECKS = {
    "screen": check_screen_recording,
    "accessibility": check_accessibility,
    "fulldisk": check_full_disk_access,
    "camera": check_camera,
}


def check_all(include_camera=True):
    """{kalit: True/False/None} qaytaradi."""
    keys = list(_CHECKS)
    if not include_camera:
        keys.remove("camera")
    out = {}
    for k in keys:
        try:
            out[k] = _CHECKS[k]()
        except Exception:
            out[k] = None
    return out


def _icon(v):
    return "✅" if v is True else ("❌" if v is False else "❓")


def report(include_camera=True):
    """Foydalanuvchiga o'zbekcha, aniq yo'l ko'rsatuvchi matn qaytaradi."""
    res = check_all(include_camera=include_camera)
    lines = ["🔐 *DODA — macOS ruxsatlari*", ""]
    missing = []
    for k, v in res.items():
        lines.append("%s %s" % (_icon(v), _TITLES[k]))
        if v is False:
            missing.append(k)
    lines.append("")
    pybin = python_path()
    if missing:
        lines.append("⚠️ Quyidagilarni yoqish kerak:")
        for k in missing:
            lines.append("")
            lines.append("• *%s*" % _TITLES[k])
            lines.append("   %s" % _PATHS[k])
            lines.append("   ➕ ro'yxatga bu ilovani qo'shing va yoqing:")
            lines.append("   `%s`" % pybin)
        lines.append("")
        lines.append("ℹ️ Yoqilgach, botni qayta ishga tushiring: «botni qayta ishga tushir»")
        lines.append("   (yoki Terminalda: `launchctl kickstart -k gui/$(id -u)/com.doda.bot`)")
    else:
        unknown = [k for k, v in res.items() if v is None]
        if unknown:
            lines.append("Aniqlab bo'lmagan: " + ", ".join(_TITLES[k] for k in unknown))
        else:
            lines.append("✅ Barcha ruxsatlar joyida — masofaviy boshqaruv to'liq ishlaydi.")
    return "\n".join(lines)


def open_settings(kind):
    """Kerakli System Settings bo'limini ochadi. kind ∈ screen/accessibility/fulldisk/camera."""
    url = _PANES.get(kind)
    if not url:
        return False
    try:
        subprocess.run(["open", url], timeout=8)
        return True
    except Exception:
        return False


def open_missing():
    """Yetishmayotgan ruxsatlar bo'limlarini ketma-ket ochadi. Ochilganlar ro'yxatini qaytaradi."""
    res = check_all()
    opened = []
    for k, v in res.items():
        if v is False:
            if open_settings(k):
                opened.append(_TITLES[k])
    return opened


def ensure_or_hint(kind):
    """kind ruxsati bormi? Bo'lsa (True, "") ; bo'lmasa (False, qisqa maslahat matni)."""
    fn = _CHECKS.get(kind)
    if not fn:
        return True, ""
    try:
        v = fn()
    except Exception:
        v = None
    if v is False:
        return False, ("%s ruxsati yo'q. %s bo'limidan «%s» ni yoqing."
                       % (_TITLES[kind], _PATHS[kind], os.path.basename(python_path())))
    return True, ""


if __name__ == "__main__":
    # Terminaldan: python3 ruxsatlar.py
    print(report().replace("*", "").replace("`", ""))
    print()
    print("Python ijro fayli:", python_path())
