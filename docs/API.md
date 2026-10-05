# DODA — Local API

> AI Engine ochadigan **yagona lokal API**. Barcha klient (Desktop, Mobile, Telegram, Web)
> shu API orqali ishlaydi. **HTTP** (so'rov/javob) + **WebSocket** (real-vaqt: ovoz holati,
> stream-javob, hodisalar). Baza: `http://127.0.0.1:8765` (lokal), tunnel orqali masofadан.
> **Versiya:** `/api/v1/*` (buzuvchi o'zgarish → `/v2`). Format: JSON. Vaqt: ISO-8601 UTC.

---

## 1. Autentifikatsiya
- Har so'rov: `Authorization: Bearer <token>` yoki `?t=<token>` (LAN) yoki Telegram initData imzosi.
- Tokenlar `api_tokens` jadvalида (xesh). `hmac.compare_digest` bilan solishtiriladi.
- Public (auth'siz): `GET /health`, `GET /` (UI). Qolgani himoyalangan.

## 2. Umumiy javob formati
```json
// muvaffaqiyat
{ "ok": true, "data": { ... } }
// xato
{ "ok": false, "error": { "code": "invalid_request", "message": "..." } }
```
Status: 200 ok · 400 noto'g'ri · 401/403 auth · 404 · 409 konflikt · 429 rate-limit · 500.

---

## 3. Endpointlar

### 🩺 Holat
| Metod | Yo'l | Auth | Tavsif |
|-------|------|:---:|--------|
| GET | `/health` | ❌ | `{ok, service, version, uptime}` — monitoring |
| GET | `/status` | ✅ | Engine holati: bot/vision/voice/scheduler, CPU/RAM, provayder, model |

### 💬 Chat / Agent
| POST | `/api/v1/chat` | ✅ | Asosiy agent kirishi |
```jsonc
// so'rov
{ "message": "ertaga majlisni eslat", "conversation_id": "…?", "stream": true }
// javob (stream=false)
{ "ok": true, "data": { "reply": "…", "lang": "uz", "conversation_id": "…",
                        "tool_calls": [ {"name":"create_task","result":{…}} ] } }
// stream=true -> WebSocket orqali token-token (quyida)
```
| GET | `/api/v1/conversation?id=…` | ✅ | Suhbat xabarlarini oladi |
| GET | `/api/v1/conversations` | ✅ | Suhbatlar ro'yxati (channel/sana bilan) |
| DELETE | `/api/v1/conversation?id=…` | ✅ | Suhbatni arxivlaydi |

### 👁️ Vision
| POST | `/api/v1/vision/analyze` | ✅ | Kadr olib LLM Vision'ga yuboradi |
```jsonc
{ "prompt": "stolda nima bor?", "device_id": "…?" }
// -> { "ok": true, "data": { "result": "…", "provider": "mac" } }
```

### 🗄️ Memory
| POST | `/api/v1/memory/search` | ✅ | Semantik qidiruv → tegishli xotiralar |
| POST | `/api/v1/memory/save` | ✅ | Fakt/xotira qo'shadi (type, content, importance) |
| GET | `/api/v1/memory?type=…` | ✅ | Xotiralarni ko'rish/filtr |
| DELETE | `/api/v1/memory?id=…` | ✅ | Soft-delete (`valid=false`) |

### ⏰ Tasks
| POST | `/api/v1/tasks/create` | ✅ | Vazifa/eslatma yaratadi (kind, schedule, payload) |
| GET | `/api/v1/tasks?status=…` | ✅ | Vazifalar ro'yxati |
| POST | `/api/v1/tasks/{id}/cancel` | ✅ | Bekor qiladi |

### 🎙️ Voice (klient mikrofon audio yuborsa)
| POST | `/api/v1/voice/transcribe` | ✅ | audio → matn (STT) |
| POST | `/api/v1/voice/speak` | ✅ | matn → audio (TTS, mp3) |

### ⚙️ Settings / Devices / Providers
| GET·PUT | `/api/v1/settings` | ✅ | Yagona config o'qish/yozish |
| GET | `/api/v1/devices?kind=camera\|mic\|speaker` | ✅ | Qurilmalar ro'yxati (tanlash uchun) |
| PUT | `/api/v1/devices/select` | ✅ | Default qurilma tanlash |
| GET·PUT | `/api/v1/providers` | ✅ | LLM provayder/model + API-key holati (kalit qiymati QAYTMAYDI) |

### 🔌 Plugins
| GET | `/api/v1/plugins` | ✅ | O'rnatilганlar |
| POST | `/api/v1/plugins/install` | ✅ | O'rnatish (source) |
| POST | `/api/v1/plugins/{id}/enable\|disable` | ✅ | Yoqish/o'chirish |
| POST | `/api/v1/plugins/{id}/update` | ✅ | Yangilash |

### 🔄 Update (desktop uchun)
| GET | `/api/v1/update/check` | ✅ | Yangi versiya bor-yo'qligi |

---

## 4. WebSocket — real-vaqt
`WS /api/v1/stream?t=<token>` — ikki tomonlama hodisalar:

```jsonc
// server -> klient (hodisalar)
{ "event": "chat.token", "conversation_id": "…", "delta": "Ert" }   // stream javob
{ "event": "voice.state", "state": "listening|thinking|speaking" }
{ "event": "task.fired", "task": { … } }
{ "event": "vision.result", "result": "…" }
{ "event": "notification", "text": "…" }
// klient -> server
{ "cmd": "voice.start" } | { "cmd": "chat", "message": "…" }
```
> Desktop/Mobile jonli avatar, ovoz holati va stream-javobni shundan oladi.

---

## 5. Tamoyillar
- **Idempotent** yozuvlar imkoni (client `request_id`).
- **Rate-limit** (429) — auth'siz + og'ir endpointlarга.
- **Pagination** — ro'yxatlarга `?limit&cursor`.
- **Versiyalash** — `/v1` barqaror; yangi maydon qo'shiladi, olib tashlanmaydi.
- Bir xil API **desktop, mobile, telegram, web** uchun — bir marta yoz, hamma joyda.
