# DODA — Version Plan (Roadmap by Release)

> **LOCKED.** Yangi feature bu rejага qo'shiladi, arxitекturани o'zgartirmaydi — faqat yangi
> **modul yoki plugin** sifatida. Har versiya oldingisi ustiga quriladi (SemVer).

---

## 🟢 v1.0 — Professional Desktop AI Assistant *(joriy maqsad)*
> Scope MUZLATILGAN — [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md).

- **Chat** (AI suhbat, uz/ru/en)
- **Claude API** (+ multi-provider registry tayyor)
- **Memory** (7-qatlam, semantik)
- **Voice** (wake → STT → TTS)
- **Vision** (Mac kamera + screen)
- **Tools** (terminal/fayl/brauzer/…)
- **Planning** (goal→plan→verify)
- **Tasks / Scheduler**
- **Plugins** (SDK + core plugin)
- **Desktop** (Flutter, o'rnatiladigan, tray, auto-update)
- **24/7 Daemon** + Local API
- **Basic Observability** (health/log)

## 🔵 v1.1 — Hardening & Integrations
- **Telegram** (plugin sifatida)
- **Better Memory** (episodic/KB chuqurroq, consolidation tuning)
- **Scheduler+** (murakkab takroriy, kalendar sync)
- **AI Evaluation** (prompt-versioning, benchmark, quality dashboard)
- **Telemetry & Analytics** (to'liq monitoring dashboard)
- **Multi-provider live** (Gemini/OpenAI/OpenRouter jonli)
- **🧠 Brain Studio (monitoring)** + **Thinking Log** + **Goals** + **Self-Review** asoslari
  ([BRAIN_STUDIO.md](BRAIN_STUDIO.md)) — Event Bus + Telemetry + Agent ustiga

## 🟣 v1.2 — Mobile
- **Mobile App** (iOS/Android — bitta Flutter codebase)
- Uy-server API'га telefon orqали ulanish
- Mobil push/notification

## 🟠 v2.0 — Autonomous & Home
- **Multi-Agent** (Main/Coding/Vision/Research/Planning orchestrator)
- **🧠 Self-Improvement** (boshqariladigan PR-oqim: Observe→Recommend→Approve→Apply) + **Learning** (kunlik tahlil) — [BRAIN_STUDIO.md](BRAIN_STUDIO.md) §4.4–4.5
- **Home AI** (mini-PC 24/7, USB kamera/mic/speaker)
- **Face Recognition** (lokal, ko'p-odam)
- **Smart Home** (Home Assistant plugin)
- **Cloud Sync** (opt-in, E2E-shifr)
- **Local LLM** (Ollama/LMStudio jonli)

## 🔴 v3.0 — Platform & Ecosystem
- **Robot / IoT** (sensor+motor integratsiyasi)
- **Multi-User** (bir DODA, ko'p foydalanuvchi)
- **Plugin Marketplace** (imzolangan katalog)
- **API Platform** (uchinchi-tomon)
- **Wear OS / Apple Watch / CarPlay / Android Auto** klientlar

---

## Versiyalash tamoyili
- **Major (x.0)** — yangi katta qobiliyat qatlami (mobil, multi-agent, robot).
- **Minor (1.x)** — yangi modul/plugin, buzuvchi bo'lmagan.
- **Patch (1.0.x)** — tuzatish/optimizatsiya.
- Har major/minor — [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) dan o'tadi.

> **Muhim:** har bir keyingi imkoniyat **4 kengaytma nuqtasi**дан biri orqали (yangi klient/plugin/provider/tool) — **arxitektura yadrosi o'zgarmaydi**. Shu sabab bu reja 5–10 yilга barqaror.
