# Changelog

Barcha muhim o'zgarishlar shu faylда hujjatlashtiriladi.
Format: [Keep a Changelog](https://keepachangelog.com/), versiyalash: [SemVer](https://semver.org/).

## [1.0.0] — 2026-08-05

Birinchi barqaror релиз. DODA to'liq ishlaydigan shaxsiy AI yordamchiga aylandi.

### Added (Qo'shildi)
- **Ovozli boshqaruv** — «Doda» uyg'otkich so'zi, davomli suhbat sessiyasi (10s jimlikда to'xtaydi).
- **Hibrid STT** — online (Google, o'zbekcha aniq) + offline (Whisper) zaxira.
- **TTS** — edge-tts o'zbek/rus ovozlari; hissiyot presetlari.
- **AI suhbat** — Claude (Haiku); javob doim o'zbekcha.
- **Agent rejimi** — fayl/kod/terminal (Claude tool-runner, sandbox + denylist).
- **Ko'rish** — kamera/ekran rasmi + AI tavsifi.
- **Yuz tanish** — lokal `face_recognition`; «meni eslab qol».
- **100k buyruq bazasi** — 133 intent, data-driven engine (100% qamrov).
- **Telegram bot** — owner-gated, ovozli xabar, masofaviy Mac boshqaruvi.
- **Veb-panel** — 3D avatar, chap menyu, tap-to-control, server-TTS.
- **Eslatma / uyg'otkich** — bir martalik, takroriy, kunlik 07:00 alarm.
- **Xizmatlar** — ob-havo, valyuta, tarjima, yangiliklar, namoz vaqtlari, hisob, kripto.
- **Uy tarmog'i nazorati** — yangi qurilma aniqlanсa ogohlantirish.
- **24/7 fon xizmatlari** — launchd (bot/dashboard/tunnel/menubar/watchdog/alarm).
- **Doimiy tunnel** — Cloudflare named tunnel (`doda.doda-ai.uz`).
- **Ommaviy portfolio** — Cloudflare Pages (`doda-ai.uz`, `www.doda-ai.uz`).
- **`/health` endpoint** — monitoring uchun.

### Security (Xavfsizlik)
- Owner-only bot (`~/.doda_owner_id`); begona urinishда egaga ogohlantirish.
- Panel auth: `hmac.compare_digest` token yoki Telegram initData HMAC imzosi.
- Cookie: `HttpOnly; SameSite=Strict` (CSRF/XSS himoyasi).
- Agent sandbox: `realpath` path-traversal himoyasi + xavfli buyruq denylist.
- Barcha sirlar uy papkasida `chmod 600`; kodда yo'q.

### Changed / Fixed (O'zgartirildi / Tuzatildi)
- Wake STT online-birinchi (o'zbekcha aniqligi + tezlik).
- AI javoblari qat'iy o'zbekcha (ingliz tili bloklangan).
- `/app` tunnel tirikligini GET bilan tekshiradi (HEAD 501 muammosi tuzatildi).
- calc_math daraja (`**`) DoS himoyasi.
- Log shovqini kamaytirildi (rumps notification, BrokenPipe, NetworkError).
- Ishlatilmayotган importlar va o'lik config tozalandi.
