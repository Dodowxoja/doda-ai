# GitHub Release Checklist — v1.0.0

Bu faylni GitHub → Releases → "Draft a new release" ga nusxalang.

---

## Release meta
- [ ] Tag: `v1.0.0`
- [ ] Target branch: `main`
- [ ] Release title: **DODA v1.0.0 — "Labbay"**
- [ ] "Set as the latest release" ✅

## Release Title
```
DODA v1.0.0 — "Labbay"
```

## Release Description (nusxalang)

```markdown
O'zbek tili uchun to'liq ishlaydigan shaxsiy sun'iy intellekt yordamchi.
Ovoz bilan gaplashadi, macOS'ni boshqaradi, ko'radi, odamlarni taniydi va
istalgan joydan (Telegram + veb-panel) boshqariladi.

🌐 Portfolio: https://doda-ai.uz

### ✨ Features
- 🎙️ Ovozli boshqaruv — «Doda» uyg'otkich so'zi, davomli suhbat
- 🧠 AI suhbat (Claude) — tabiiy o'zbekcha
- 🛠️ Agent rejimi — fayl/kod/terminal
- 👁️ Ko'rish + 🙂 yuz tanish (lokal)
- 📱 Masofaviy boshqaruv — Telegram bot + veb-panel (3D avatar, tap-to-control)
- ⏰ Eslatma/uyg'otkich · 🌐 ob-havo/valyuta/tarjima/yangiliklar/namoz
- 🏠 Uy tarmog'i nazorati · ♾️ 24/7 (launchd)

### 🔒 Security
- Owner-only bot; begona urinishда ogohlantirish
- Panel: constant-time token + Telegram HMAC imzosi
- Cookie HttpOnly + SameSite=Strict (CSRF/XSS)
- Agent sandbox (realpath) + xavfli buyruq denylist
- Sirlar chmod 600, kodда yo'q

### 💥 Breaking Changes
Yo'q (birinchi релиз).

### ⚠️ Known Issues
- Offline o'zbek STT (Whisper) aniqligi past — online yaxshi
- TTS bepul edge-tts bilan cheklangan
- Telegram Mini App webview'да mikrofon yo'q (ovozли xabar/Chrome ishlating)
- Rate limiting yo'q (Cloudflare edge + auth qoplaydi)

To'liq: CHANGELOG.md · RELEASE_NOTES.md · README.md
```

## Release oldidan tekshiruv (pre-flight)
- [ ] `python3 -m py_compile *.py` — toza
- [ ] `pip install -r requirements.txt` — ishlaydi
- [ ] Barcha 6 launchd servis yuklanган va ishlayapti
- [ ] `README.md`, `LICENSE`, `CHANGELOG.md`, `VERSION` mavjud
- [ ] Sirlar (`~/.doda_*`) repoда YO'Q (`.gitignore` bilan himoyalangan)
- [ ] `doda-ai.uz` va `doda.doda-ai.uz` ochiladi
