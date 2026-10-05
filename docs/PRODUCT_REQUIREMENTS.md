# DODA v1.0 — Product Requirements (PRD)

> **v1.0 scope MUZLATILGAN (FROZEN).** Yangi feature qo'shilmaydi — faqat quyidagilar tugatiladi.
> Priority: **P0** (majburiy) · **P1** (kerak, slip mumkin) · **P2** (yaxshi bo'lardi).
> Status: `Planned` / `In Progress` / `Done`. Dependencies = modul ([ROADMAP](../doda/ROADMAP.md)).

---

## v1.0 imkoniyatlari

### F1 — Foundation (infra)
- **Description:** Portlar, modellar, config, DI, Event Bus, Observability, feature-flags.
- **Priority:** P0 · **Deps:** — · **Status:** In Progress (Modul 1)
- **Acceptance:** portlar import; EventBus pub/sub; config yuklaydi; `pytest`+`mypy`+`ruff`+`black` yashил; contract-test ramkasi.

### F2 — AI Chat (Claude, multi-provider ready)
- **Description:** Claude API bilan tabiiy suhbat (uz/ru/en); provider-registry (Gemini/OpenAI/… stub).
- **Priority:** P0 · **Deps:** F1 · **Status:** Planned (M2)
- **Acceptance:** Claude'дан real javob; stream; tool-calling; provider config'дан tanlanadi; token/cost qayd etiladi.

### F3 — Memory (7-layer)
- **Description:** Working/Conversation/Episodic/Semantic/Long-term/Profile/KB; semantik qidiruv.
- **Priority:** P0 · **Deps:** F1 · **Status:** Planned (M3)
- **Acceptance:** fakt saqlaydi; semantik `search` tegishlini topadi; keyingi sessiyada eslaydi; SQLite'да persist.

### F4 — Agent Kernel (cognitive)
- **Description:** Recall→Act→Reflect tsikli; persona; suhbat + tool orkestrovka.
- **Priority:** P0 · **Deps:** F2, F3 · **Status:** Planned (M4)
- **Acceptance:** persona+xotira bilan suhbat; tool chaqiradi; eventlar oqadi; kontekst inject.

### F5 — Vision (Perception)
- **Description:** Mac kamera + screen; "Nima ko'ryapsan?" → Claude Vision. Env-sensorlar (clipboard/time/active-window).
- **Priority:** P0 · **Deps:** F4 · **Status:** Planned (M5)
- **Acceptance:** Mac kameradан kadr → tavsif; kamera provider config'дан; env-kontekst agentга.

### F6 — Tools
- **Description:** Terminal/Files/Clipboard/Notification/Weather/Calendar/Browser (sandbox + tasdiq).
- **Priority:** P0 · **Deps:** F4 · **Status:** Planned (M6)
- **Acceptance:** AI tool bilan real ish; xavfsizlik (denylist/sandbox); `tool_history` audit.

### F7 — Planning Engine
- **Description:** Goal→plan→subtask→execute→verify→retry.
- **Priority:** P1 · **Deps:** F4, F6 · **Status:** Planned (M7)
- **Acceptance:** murakkab goal reja bilan bajariladi; xatoда replan (cheklangan).

### F8 — Voice (wake→STT→agent→TTS)
- **Description:** "DODA/Hey DODA" wake; STT; ovozли javob (TTS).
- **Priority:** P0 · **Deps:** F5, F6 · **Status:** Planned (M8)
- **Acceptance:** wake ishlaydi; suhbat davom etadi; jimlik'да to'xtaydi; uz ovoz.

### F9 — Tasks / Scheduler
- **Description:** "Ertaga eslat / har juma backup"; bir martalik + cron.
- **Priority:** P0 · **Deps:** F4 · **Status:** Planned (M9)
- **Acceptance:** vazifa yaratiladi, o'z vaqtида bajariladi; persist (restart'дан keyin).

### F10 — Plugin SDK + core plugins
- **Description:** `doda.sdk`, manifest, hot-reload, permission; Web-dashboard plugin sifatida.
- **Priority:** P0 · **Deps:** F6 · **Status:** Planned (M10)
- **Acceptance:** plugin o'rnatiladi/yoqiladi; core tegilmaydi; restartsiz enable/disable.

### F11 — Desktop App (Flutter)
- **Description:** O'rnatiladigan UI (Chat/Settings/Memory/Tasks/Vision/Plugins/Logs); tray; autostart; auto-update.
- **Priority:** P0 · **Deps:** F2–F10 (API) · **Status:** Planned (Track B D1–D9)
- **Acceptance:** DMG/EXE/AppImage/DEB o'rnatiladi; tray; Settings'дан device/key; chat UI jonli.

### F12 — 24/7 Daemon + Local API
- **Description:** OS-service (boot autostart), WebSocket+HTTP API, eski v1.0.0 almashtirish.
- **Priority:** P0 · **Deps:** F1–F10 · **Status:** Planned (M12)
- **Acceptance:** bitta jarayon hammasini yuritadi; boot'да ishga tushadi; API auth bilan.

### F13 — Basic Observability & Health (P1)
- **Description:** Strukturali log, `/health` `/status`, asosiy metrika (to'liq AI-Eval/Telemetry → v1.1).
- **Priority:** P1 · **Deps:** F1 · **Status:** Planned (M1 hooks, M14 basic)
- **Acceptance:** `/health` 200; loglar strukturали; xato kuzatiladi.

---

## Xulosa
**v1.0 = 13 feature** (F1–F13). Bulardan tashqarisi — [VERSION_PLAN.md](VERSION_PLAN.md) keyingi versiyalar,
[NON_GOALS.md](NON_GOALS.md) v1.0'да YO'Q. Barcha feature [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) DoD'siга bo'ysunadi.
