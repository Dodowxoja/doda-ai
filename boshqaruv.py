# -*- coding: utf-8 -*-
"""DODA — uzoqdan tap-to-control: sichqoncha va klaviatura hodisalarini yuboradi.

Quartz (CGEvent) orqali ishlaydi — Accessibility ruxsati kerak (berilgan).
web_dashboard.py (Mini App) shu funksiyalarni chaqiradi: foydalanuvchi ekran
rasmiga bosadi -> shu joyga klik; matn yozadi -> klaviaturaga yuboriladi.

Koordinatalar KASR (0..1) sifatida keladi (rasmning qaysi qismiga bosildi),
bu yerda displey o'lchamiga ko'paytiriladi -> retina/masshtab muammosi bo'lmaydi.
"""
import time
import subprocess

try:
    import Quartz
    _OK = True
except Exception:
    _OK = False


def available():
    return _OK


def screen_size():
    """Asosiy displey o'lchami (NUQTALARда — CGEvent mouse koordinatalari shu tizimда)."""
    b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return float(b.size.width), float(b.size.height)


def _post(ev):
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def _mouse(x, y, etype, button, clickstate=1):
    ev = Quartz.CGEventCreateMouseEvent(None, etype, (x, y), button)
    if clickstate > 1:
        Quartz.CGEventSetIntegerValueField(ev, Quartz.kCGMouseEventClickState, clickstate)
    _post(ev)


def click(x, y, button="left", double=False):
    """(x, y) NUQTALARDA klik qiladi."""
    x, y = float(x), float(y)
    if button == "right":
        down, up, btn = (Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp,
                         Quartz.kCGMouseButtonRight)
    else:
        down, up, btn = (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp,
                         Quartz.kCGMouseButtonLeft)
    _mouse(x, y, Quartz.kCGEventMouseMoved, btn)
    time.sleep(0.02)
    _mouse(x, y, down, btn, 1)
    _mouse(x, y, up, btn, 1)
    if double:
        time.sleep(0.05)
        _mouse(x, y, down, btn, 2)
        _mouse(x, y, up, btn, 2)


def click_fraction(xf, yf, button="left", double=False):
    """Kasr (0..1) koordinata bo'yicha klik (rasmning qaysi qismiga bosilgani)."""
    w, h = screen_size()
    xf = max(0.0, min(1.0, float(xf)))
    yf = max(0.0, min(1.0, float(yf)))
    click(xf * w, yf * h, button=button, double=double)


def scroll(direction="down", amount=5):
    dy = -abs(amount) if direction == "down" else abs(amount)
    ev = Quartz.CGEventCreateScrollWheelEvent(None, Quartz.kCGScrollEventUnitLine, 1, dy)
    _post(ev)


# Klaviatura: nom -> macOS virtual keycode
_KEYCODES = {
    "enter": 36, "return": 36, "esc": 53, "escape": 53, "backspace": 51,
    "delete": 51, "tab": 48, "space": 49, "up": 126, "down": 125,
    "left": 123, "right": 124, "home": 115, "end": 119,
}
_LETTER = {"v": 9, "c": 8, "a": 0, "x": 7, "z": 6}


def _key(keycode, flags=0):
    d = Quartz.CGEventCreateKeyboardEvent(None, keycode, True)
    if flags:
        Quartz.CGEventSetFlags(d, flags)
    _post(d)
    u = Quartz.CGEventCreateKeyboardEvent(None, keycode, False)
    if flags:
        Quartz.CGEventSetFlags(u, flags)
    _post(u)


def press_key(name):
    """Maxsus tugma bosadi (enter/esc/backspace/tab/strelka...). True/False."""
    kc = _KEYCODES.get((name or "").lower())
    if kc is None:
        return False
    _key(kc)
    return True


def type_text(text):
    """Matnni yozadi. Unicode (o'zbek/rus/emoji) uchun ishonchli: clipboard -> Cmd+V."""
    if not text:
        return
    subprocess.run(["pbcopy"], input=text.encode("utf-8"))
    time.sleep(0.05)
    _key(_LETTER["v"], Quartz.kCGEventFlagMaskCommand)   # Cmd+V


if __name__ == "__main__":
    print("Quartz mavjud:", available())
    if available():
        print("Ekran o'lchami (nuqtalar):", screen_size())
