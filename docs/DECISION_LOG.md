# DODA — Decision Log (ADR)

> Barcha muhim arxitektura/loyiha qarorlari va **sabablari**. Kelajакда "nega shunday?" degan
> savolга javob. Format: ADR (Architecture Decision Record). Har qaror — **LOCKED**;
> o'zgartirish yangi ADR talab qiladi.

---

### ADR-001 — Backend tili: **Python**
- **Qaror:** AI Engine Python 3.13'да.
- **Sabab:** AI/ML ekotizimi (anthropic, whisper, opencv, face_recognition) Python'да yetuk; mavjud v1.0.0 Python; jamoa tajribasi.
- **Alternativlar:** Node (ML zaif), Rust (ML kam), Go (ML kam). — rad.

### ADR-002 — Frontend: **Flutter** (Tauri/Electron emas)
- **Qaror:** UI Flutter'да (Desktop + Mobile bitta codebase).
- **Sabab:** foydalanuvchi Flutter-dev; kelajакда iOS/Android bir codebase; native unum; uzoq-muddat.
- **Alternativlar:** Tauri (mobil zaif, web-UI reuse), Electron (og'ir 150MB). — rad. *(Tradeoff: web-UI Dart'да qaytadan.)*

### ADR-003 — IPC: **WebSocket + HTTP (JSON)** (gRPC emas)
- **Qaror:** Flutter↔Python + barcha klient WebSocket+HTTP orqali.
- **Sabab:** **bitta API yuzasi** barcha klient uchun (Flutter/web/telegram/mobil); brauzer native qo'llaydi; Flutter yetuk.
- **Alternativ:** gRPC — web uchun grpc-web proksi kerak, ikki yuza. — kelajак ixtiyoriy.

### ADR-004 — **Clean Architecture + SOLID**
- **Qaror:** qatlamli (domain/application/infra/delivery), DIP.
- **Sabab:** 5–10 yil barqarorlik; test-oson; provider almashtiriladi; yadro o'zgarmaydi.
- **Xarajat:** ko'proq abstraktsiya — YAGNI bilan boshqariladi.

### ADR-005 — **Event Bus (Event-Driven)**
- **Qaror:** modullararo aloqa pub/sub (lokal asyncio bus).
- **Sabab:** modullar bir-birini bilmaydi (Open/Closed); yangi plugin faqat obuna; ChatGPT/Cursor-uslub decoupling.
- **Chegara:** event = decoupling nuqtasi; sync = to'g'ridan (haddan ortiq emas). Broker (NATS/Redis) — post-M12.

### ADR-006 — **Provider-Agnostic** (LLM/Vision/Memory/Speech)
- **Qaror:** har xizmat port ortида; registry config'дан tanlaydi.
- **Sabab:** vendor-lock yo'q; Claude→Gemini/OpenAI/lokal almashtiriladi kod tegilmасдан; fallback.

### ADR-007 — DB: **SQLite** (SQLModel bilan, Postgres emas — hozir)
- **Qaror:** lokal SQLite; SQLModel/SQLAlchemy abstraktsiya.
- **Sabab:** bitta qurilma; local-first; kutubxonасiz (built-in); Postgres = URL o'zgarishi (ko'p-qurilma/mini-PC'да).

### ADR-008 — **Local-first + secrets in OS Keychain**
- **Qaror:** ma'lumot qurilmада; sirlar keychain'да (kodда/DB'да emas); DB shifri.
- **Sabab:** maxfiylik; kompyuter-boshqaruv uchun to'g'ri xavfsizlik pozasi.

### ADR-009 — **Plugin-First + SDK**
- **Qaror:** core minimal; funksiyalar (Telegram/Web/Camera) plugin sifatida; `doda.sdk`.
- **Sabab:** yangi imkoniyat core'ni buzmaydi; hot-reload; ekotizim (kelajак marketplace).

### ADR-010 — **Cognitive Agent** (Perceive→Plan→Act→Verify→Reflect)
- **Qaror:** agent = kognitiv tsikl, chat-loop emas; Planning + Perception + 7-layer Memory.
- **Sabab:** haqiqiy agent (ChatGPT/Cursor darajasi); murakkab goal'ни bajaradi; xotira+sezgi.

### ADR-011 — **DI: qo'lда Composition Root** (`container.py`)
- **Qaror:** dependency-injection kutubxонаsiz, qo'lда container.
- **Sabab:** yengil, aniq, test-oson, ortiqcha dep yo'q.

### ADR-012 — **Config: pydantic-settings** (yagona sxema)
- **Qaror:** bitta tiplangan config sxema (TOML+env), per-OS yo'l abstraktsiya.
- **Sabab:** "bitta unified config"; validatsiya; xavfsiz.

### ADR-013 — **Scope Freeze: v1.0 = 13 feature**
- **Qaror:** v1.0 scope MUZLATILGAN (PRD); yangi feature v1.0'га EMAS, VERSION_PLAN'га.
- **Sabab:** scope-creep'дан himoya; MVP'ни professional tugatish; eng katta risk (T1) nazorati.

### ADR-014 — **Enterprise standartlar majburiy**
- **Qaror:** har modul Clean/SOLID/async/type/test/mypy/ruff/black/DoD; vaqtinchalik kod yo'q.
- **Sabab:** 5–10 yil rivojlanadigan professional platforma; sifat > tezlik.

### ADR-015 — **Yangi `doda/` paketi eski v1.0.0 yonida** (in-place refactor emas)
- **Qaror:** yangi arxitektura alohida paketда; eski flat-kod parity'gача ishlab turadi.
- **Sabab:** ishlaydigan tizimni buzmaslik; modul-ba-modul xavfsiz migratsiya.

### ADR-016 — **DODA Brain (Claude = reasoning engine)**
- **Qaror:** DODA — mustaqil "aql" (Memory/Goals/Planning/Learning/Self-Review orkestratsiyasi);
  Claude/LLM faqat almashtiriladigan **fikrlash vositasi**.
- **Sabab:** vendor-lock yo'q; DODA identifikatsiyasi modeldan mustaqil; AI-OS darajasi.
- **Natija:** Brain Studio — shu aqlning cockpit'i ([BRAIN_STUDIO.md](BRAIN_STUDIO.md)).

### ADR-017 — **Autonomy Boundary (o'z-o'zini o'zgartirmaslik)** 🔒
- **Qaror:** DODA HECH QACHON yashirin/avtomatik o'zini (kod/muhim-config) o'zgartirmaydi.
  Self-Improvement faqat **taklif** (patch/PR) beradi; qo'llash **foydalanuvchi tasdig'idan keyin**.
- **Sabab:** xavfsizlik majburiy qoidasi; kompyuter-boshqaruvchi agent uchun ishonch chegarasi.
- **Oqim:** Observe → Analyze → Recommend → PR/Patch → **User Approval** → Apply.

---

## Qoida
Yangi muhim qaror → shu logга **yangi ADR** qo'shiladi (o'chirilmaydi). Eski qarorни o'zgartirish
→ "ADR-XXX supersedes ADR-YYY" bilan qayd etiladi. Qarorlar unutilmaydi.
