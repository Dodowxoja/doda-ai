# DODA — Design Documentation (Design Bible)

> DODA platformasining to'liq system design'i. Modul kodini yozishdan **oldin** tayyorlangan —
> 5–10 yil o'zgarmaydigan puxta poydevor uchun. Modul 1 kodi faqat shu hujjatlar review'дан
> o'tgach boshlanadi.

## Hujjatlar

| # | Hujjat | Nima haqida |
|---|--------|-------------|
| 1 | [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) | Butun platforma high-level arxitekturasi + diagrammalar |
| 2 | [DATABASE.md](DATABASE.md) | Barcha jadvallar (users…voice_history) + ER + retention |
| 3 | [API.md](API.md) | Lokal API (HTTP + WebSocket) — barcha klient uchun |
| 4 | [DESKTOP.md](DESKTOP.md) | Desktop app oqimi (UI→API→Engine→LLM→Memory→Plugins→Tools) |
| 5 | [SECURITY.md](SECURITY.md) | Kalitlar, DB shifri, secrets, loglar, privacy, trust-zonalar |
| 6 | [PLUGINS.md](PLUGINS.md) | Plugin SDK, lifecycle, permission, install/update |
| 7 | [FUTURE.md](FUTURE.md) | Multi-user, Home AI, Smart Home, Phone, Watch, Car… |
| 8 | [UI_GUIDE.md](UI_GUIDE.md) | Desktop ekranlari (Splash/Chat/Brain-Studio/Settings/Memory/Tasks/Plugins/Logs/Vision/Developer) |
| 8b | [BRAIN_STUDIO.md](BRAIN_STUDIO.md) | 🧠 DODA Brain + Brain Studio cockpit (Thinking Log/Goals/Self-Review/Self-Improvement/Learning + Autonomy Boundary) |

| 9 | [ENGINEERING_STANDARDS.md](ENGINEERING_STANDARDS.md) | Har modul majburiy sifat standartlari (Clean/SOLID/test/mypy/DoD) |

## Mahsulot va boshqaruv (Product & Governance) — 🔒 v1.0 FROZEN
| Hujjat | Nima haqida |
|--------|-------------|
| [VISION.md](VISION.md) | DODA nima/kim uchun; 1/3/5 yillik maqsad |
| [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | v1.0 = 13 feature (priority/deps/status/acceptance) |
| [VERSION_PLAN.md](VERSION_PLAN.md) | Featureлар versiyalarга (v1.0→v3.0) |
| [NON_GOALS.md](NON_GOALS.md) | v1.0'да NIMA BO'LMAYDI (scope guard) |
| [RISK_REGISTER.md](RISK_REGISTER.md) | Barcha xavflar (P/I/mitigation) |
| [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) | Production release checklist |
| [DECISION_LOG.md](DECISION_LOG.md) | 15 ADR — har qarorning sababi |

## Bog'liq hujjatlar
- [../doda/ARCHITECTURE.md](../doda/ARCHITECTURE.md) — AI Engine (Python) ichki arxitekturasi
- [../doda/ROADMAP.md](../doda/ROADMAP.md) — Engine modullari (M1–M14)
- [../doda/ARCHITECTURE_REVIEW.md](../doda/ARCHITECTURE_REVIEW.md) — Senior-architect audit (13/13, risklar, tavsiyalar)
- [../desktop/DESKTOP_ARCHITECTURE.md](../desktop/DESKTOP_ARCHITECTURE.md) — Flutter paketlash, installer, CI/CD (D1–D10)

## Asosiy qarorlar (o'zgarmas poydevor)
- **Flutter + Python** (frontend/backend alohida; desktop+mobil bitta codebase)
- **Local-first · API-centric · Provider-agnostic**
- **SQLite → Postgres** (SQLModel), **secrets → OS keychain**
- **4 kengaytma nuqtasi:** yangi klient / plugin / provider / tool — core o'zgarmaydi

## Holat: 🔒 LOCKED (2026-08-05)
Architecture · Scope (v1.0 = 13 feature) · Version Plan — **MUZLATILGAN.** Yangi feature
arxitекturани o'zgartirmaydi — faqat yangi modul/plugin. Keyingi qadam: **Modul 1 (Foundation)** implementatsiyasi.
