# DODA v1.0.0 — Release Notes

**Sana:** 2026-08-05
**Kod nomi:** "Labbay"

DODA'ning birinchi barqaror релизи — o'zbek tili uchun to'liq ishlaydigan shaxsiy
sun'iy intellekt yordamchi. Ovoz bilan gaplashadi, kompyuterni boshqaradi, ko'radi,
odamlarni taniydi va istalgan joydan boshqariladi.

---

## ✨ Asosiy imkoniyatlar

- 🎙️ **Ovozli boshqaruv** — «Doda» deб chaqiring, davomli suhbat.
- 🧠 **AI suhbat** (Claude) — tabiiy o'zbekcha javoblar.
- 🛠️ **Agent rejimi** — fayl/kod/terminal ishlarини o'zi bajaradi.
- 👁️ **Ko'rish + yuz tanish** — kamera/ekran, odamlarni ism bilan eslaydi.
- 📱 **Masofaviy boshqaruv** — Telegram bot + veb-panel (3D avatar, tap-to-control).
- ⏰ **Eslatma / uyg'otkich** + 🌐 **xizmatlar** (ob-havo, valyuta, tarjima, yangiliklar…).
- 🏠 **Uy tarmog'i nazorati** · ♾️ **24/7** (launchd).

## 🔒 Xavfsizlik yaxshilanishlari

- Faqat ega boshqaradi; begona urinishда ogohlantirish.
- Panel: constant-time token + Telegram HMAC imzosi.
- Cookie: `HttpOnly; SameSite=Strict` (CSRF/XSS).
- Agent sandbox + xavfli buyruq denylist.
- Sirlar `chmod 600`, kodда yo'q.

## 🌐 Infratuzilma

- `doda-ai.uz` + `www.doda-ai.uz` — ommaviy portfolio (Cloudflare Pages, doim ochiq).
- `doda.doda-ai.uz` — maxfiy boshqaruv paneli (doimiy Cloudflare named tunnel).

## ⚠️ Ma'lum cheklovlar (Known Issues)

- **Offline o'zbek STT (Whisper)** aniqligi past — online (Google) ishlatilganда yaxshi.
  Kelajakда: o'z modeli / voice-cloning (kuchli Mac olингач).
- **TTS ovozi** — bepul edge-tts bilan cheklangan (voice-cloning rejada).
- **Telegram Mini App webview'да mikrofon** ishlamaydi — ovozли xabar yoki Chrome ishlating.
- **Rate limiting yo'q** — Cloudflare edge + auth qoplaydi (kelajak yaxshilanishi).

## 💥 Breaking Changes

Yo'q — bu birinchi релиз.

## 📦 O'rnatish

`README.md` ga qarang: tizim kutubxonalari (portaudio/ffmpeg/cmake) + `pip install -r requirements.txt` + maxfiy fayllarни sozlash.
