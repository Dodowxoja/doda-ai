# DODA — Shaxsiy Sun'iy Intellekt Yordamchi

DODA — o'zbek, rus va ingliz tilida gaplashadigan, macOS kompyuterini **ovoz bilan**
boshqaradigan, sun'iy intellekt bilan suhbatlashadigan va masofadan (Telegram + veb-panel)
boshqariladigan shaxsiy yordamchi.

- 🌐 Portfolio: <https://doda-ai.uz>
- 🔒 Boshqaruv paneli: `https://doda.doda-ai.uz` (faqat egaga, token bilan)
- 🤖 Telegram bot: [@voice_doda_bot](https://t.me/voice_doda_bot)

---

## Imkoniyatlar

| Modul | Tavsif |
|-------|--------|
| 🎙️ Ovozli boshqaruv | «Doda» uyg'otkich so'zi bilan tinglaydi; 130+ buyruq turi (ilova/sayt ochish, tizim, media, dev) |
| 🧠 AI suhbat | Claude (Haiku) bilan tabiiy o'zbekcha suhbat |
| 🛠️ Agent rejimi | Fayl/kod yozadi, terminal buyruqlarини bajaradi (Claude tool-runner) |
| 👁️ Ko'rish | Kamera/ekran rasmi + AI tavsifi |
| 🙂 Yuz tanish | Odamlarni ism bilan eslab qoladi (lokal `face_recognition`) |
| 📱 Masofaviy boshqaruv | Telegram bot + veb-panel (ekran, kamera, sichqoncha/klaviatura) |
| ⏰ Eslatma/uyg'otkich | Bir martalik, takroriy, uyg'otish alarmi |
| 🌐 Xizmatlar | Ob-havo, valyuta, tarjima, yangiliklar, namoz vaqtlari, hisob |
| 🏠 Tarmoq nazorati | Uy Wi-Fi'ga kim ulanganini kuzatadi |

---

## Arxitektura

**Asosiy modullar:**
- `asistent.py` — dvigatel: STT/TTS, buyruq dispetcheri, NLU, AI/agent, eslatma, yuz.
- `telegram_bot.py` — Telegram bot (owner-gated, OTP-siz qo'lда ega belgilanadi).
- `web_dashboard.py` — veb-panel (stdlib `http.server`, port 8765, token/initData auth).
- `dashboard.html` / `avatar.html` — panel UI (chap menyu + 3D avatar).
- `vision.py`, `tarmoq.py`, `mac_system.py`, `ruxsatlar.py`, `boshqaruv.py`, `agent_tools.py` — yordamchi modullar.
- `tunnel.py`, `watchdog.py`, `uygotkich.py`, `menubar.py` — fon xizmatlari.

**Ma'lumot (kod EMAS):**
- `data/buyruqlar.json`, `data/javoblar.json` — asosiy buyruq/javob bazasi.
- `data/foydalanuvchi.json` — foydalanuvchi qo'shган buyruqlar (bazadan ustun).

**Fon xizmatlari (launchd):**

| Xizmat | Vazifa |
|--------|--------|
| `com.doda.bot` | Telegram bot 24/7 |
| `com.doda.dashboard` | Veb-panel (8765) |
| `com.doda.tunnel` | Cloudflare tunnel (`doda.doda-ai.uz`) |
| `com.doda.menubar` | macOS menyu-bar ilovasi |
| `com.doda.watchdog` | Bot heartbeat kuzatuvchi (120s) |
| `com.doda.alarm` | Kunlik uyg'otkich (07:00) |

---

## O'rnatish

**Talab:** macOS (Apple Silicon), Python 3.13 (pyenv tavsiya etiladi).

```bash
# 1) Tizim kutubxonalari (Homebrew)
brew install portaudio ffmpeg cmake

# 2) Python paketlari
pip install -r requirements.txt
#   Eslatma: face_recognition uchun setuptools<81 shart (pkg_resources), requirements'да bor.
```

---

## Sozlash (maxfiy fayllar)

Sirlar **hech qачон kodда yoki repozitoriyда saqlanmaydi** — barchasi uy papkangizda,
`chmod 600` bilan:

| Fayl | Mazmuni | Qanday olinadi |
|------|---------|----------------|
| `~/.doda_claude_key` | Anthropic API kaliti | console.anthropic.com |
| `~/.doda_bot_token` | Telegram bot tokeni | @BotFather |
| `~/.doda_web_token` | Panel maxfiy tokeni | avtomatik yaratiladi |
| `~/.doda_owner_id` | Egasining Telegram ID'si | `echo <ID> > ~/.doda_owner_id` |
| `~/.doda_named_tunnel` | Doimiy tunnel (nom + URL) | `TUNNEL_SETUP.md` |

**Muqobil muhit o'zgaruvchilari** (fayl o'rniga):
```bash
export ANTHROPIC_API_KEY="sk-ant-..."     # ⚠️ faqat v1.0.0 (asistent.py) uchun
export TELEGRAM_BOT_TOKEN="..."
```

> **v2 engine (`doda/` paketi, dashboard/API) BOSHQA nomdan o'qiydi** — `ANTHROPIC_API_KEY` EMAS:
> ```bash
> export DODA_SECRET_ANTHROPIC_KEY="sk-ant-..."   # SecretStore kaliti: anthropic.key
> python -m doda.interfaces.api
> ```
> yoki `~/Library/Application Support/DODA/secrets.json` (0600): `{ "anthropic.key": "sk-ant-..." }`

> ⚠️ Kalit/tokenni hech qачон chatga yoki kodга yozmang. Tasodifan yozilса — darhol
> bekor qilib (revoke) yangisini oling.

---

## Ishga tushirish

**Desktop (ovoz):**
```bash
python asistent.py          # «Doda» deb chaqiring
```

**Fon xizmatlari (24/7, launchd):**
```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.doda.bot.plist
# Kodни o'zgartirgach qayta ishga tushirish:
launchctl kickstart -k gui/$(id -u)/com.doda.bot
# To'xtatish:
launchctl bootout gui/$(id -u)/com.doda.bot
```

**Veb-panel:** `http://localhost:8765/?t=<token>` yoki Telegram'да `/app`.

---

## Deployment

**1) Doimiy tunnel (boshqaruv paneli — `doda.doda-ai.uz`):**
To'liq qo'llanma — [`TUNNEL_SETUP.md`](TUNNEL_SETUP.md). Qisqacha:
```bash
cloudflared tunnel login
cloudflared tunnel create doda
cloudflared tunnel route dns doda doda.doda-ai.uz
# ~/.cloudflared/config.yml + ~/.doda_named_tunnel sozlanadi
launchctl kickstart -k gui/$(id -u)/com.doda.tunnel
```

**2) Portfolio (`doda-ai.uz` — Cloudflare Pages):**
```bash
wrangler login
wrangler pages deploy portfolio --project-name=doda-ai --branch=main
# Custom domain: doda-ai.uz + www.doda-ai.uz (Cloudflare panelda CNAME @ -> doda-ai.pages.dev, proxied)
```

---

## Veb-panel API

Barcha `/api/*` **auth talab qiladi** (`?t=<token>`, cookie yoki Telegram initData imzosi).

| Endpoint | Metod | Auth | Tavsif |
|----------|-------|------|--------|
| `/health` | GET | ❌ | Sog'liq tekshiruvi (`{ok, bot}`) |
| `/` | GET | ❌ | Panel UI (maxfiy ma'lumotsiz) |
| `/api/status` | GET | ✅ | Batareya/CPU/RAM/bot holati |
| `/api/network` | GET | ✅ | Uy tarmog'i qurilmalari |
| `/api/logs` | GET | ✅ | Xatolar jurnali |
| `/api/permissions` | GET | ✅ | macOS ruxsatlari |
| `/api/screenshot` `/api/camera` | GET | ✅ | Ekran/kamera rasmi |
| `/api/tts?text=` | GET | ✅ | Matnни o'zbek ovoziga (mp3) |
| `/api/command` | POST | ✅ | Buyruq bajarish |
| `/api/click` `/api/type` `/api/key` `/api/scroll` | POST | ✅ | Masofaviy sichqoncha/klaviatura |

---

## Xavfsizlik

- Panel: maxfiy token (`hmac.compare_digest`) yoki Telegram initData HMAC imzosi.
- Cookie: `HttpOnly; SameSite=Strict` (CSRF/XSS himoyasi).
- Bot: faqat ega (`~/.doda_owner_id`); begona urinish egaga ogohlantirish yuboradi.
- Agent/terminal: `WORKSPACE` sandbox (`realpath`), xavfli buyruq denylist, tasdiqlash tugmasi.
- Sirlar: fayllarда `chmod 600`, kodда yo'q.

---

## Muammolarni bartaraf qilish (Troubleshooting)

| Muammo | Yechim |
|--------|--------|
| Panel «Ruxsat yo'q» | Tokensiz ochilган — Telegram'да `/app` orqali oching (token bilan) |
| Ekran/kamera «olinmadi» | System Settings → Privacy → Screen Recording/Camera'га launchd python'ni qo'shing, so'ng `kickstart` |
| «Doda» eshitilmayapti | `asistent.py`ни qayta ishga tushiring; barqaror tarmoqда sinang |
| Mini App ochilmaydi | `/app`ни qayta yuboring (yangi token/URL); tunnel `kickstart` |
| Bot javob bermaydi | `launchctl print gui/$(id -u)/com.doda.bot` holatini tekshiring; `logs/.doda_errors.log` |
| Ovoz inglizcha | Tuzatilган — DODA doim o'zbekcha (agar eski jarayon bo'lsa qayta ishga tushiring) |

---

## Litsenziya va muallif

Yaratuvchi: **Muhammadxo'ja** ([github.com/Dodowxoja](https://github.com/Dodowxoja)).
Shaxsiy loyiha — o'zbek tili uchun sun'iy intellekt yordamchi.
