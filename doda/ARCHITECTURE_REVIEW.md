# DODA — Architecture Review (Senior Software Architect Audit)

> Sana: 2026-08-05 · Ko'lam: `ARCHITECTURE.md` (v2) + `ROADMAP.md` (v2) + `../docs/*`.
> Maqsad: ChatGPT/Claude-Desktop/Cursor darajasi; 5–10 yil o'zgarmaydigan poydevor.

---

## 1. Talablar qamrovi (13 nuqta)

| # | Talab | Holat | Qayerda |
|---|-------|:-----:|---------|
| 1 | Desktop App (mac/win/linux, FE/BE alohida, Flutter-ready) | ✅ | DESKTOP.md, DESKTOP_ARCHITECTURE.md — API-centric ⇒ UI-framework almashtiriladi |
| 2 | Multi-Provider (Claude/Gemini/OpenAI/Ollama/LMStudio/OpenRouter/future) | ✅ | ARCH §7 — LLMProvider port + registry |
| 3 | Advanced Memory (7 qatlam) | ✅ **qo'shildi** | ARCH §5 — Working…Knowledge Base |
| 4 | Perception (Vision/Audio/Environment) | ✅ **qo'shildi** | ARCH §4a — yagona sezgi abstraksiyasi |
| 5 | Planning Engine (goal→plan→verify→retry) | ✅ **qo'shildi** | ARCH §4b — Planner/Executor/Verifier |
| 6 | Multi-Agent (Main/Coding/Vision/Research/Planning) | ✅ **qo'shildi** | ARCH §6 — Orchestrator, kelajak-tayyor |
| 7 | Plugin SDK (lifecycle/permission/hot-reload/version) | ✅ | PLUGINS.md + ARCH §10 |
| 8 | Security (keys/permission/encrypt/secrets/audit/sandbox) | ✅ | SECURITY.md |
| 9 | Observability (log/metric/trace/crash/health) | ✅ **qo'shildi** | ARCH §8 |
| 10 | Desktop Installer (CI/CD, DMG/EXE/AppImage/DEB) | ✅ | DESKTOP_ARCHITECTURE.md D6–D8 |
| 11 | Future Home AI | ✅ | FUTURE.md, SYSTEM_DESIGN.md |
| 12 | Event Bus (Pub/Sub, decoupling) | ✅ **qo'shildi** | ARCH §3 — core primitiv |
| 13 | Final Review | ✅ | shu hujjat |

**Xulosa:** 13/13 arxitektura darajasida qamrab olindi (6 tasi shu auditда kuchaytirildi).

---

## 2. ✅ Kuchli joylar (nima yaxshi)

1. **To'g'ri kengaytma nuqtalari** — yangi *klient / plugin / provider / tool / event-obunachi* qo'shiladi, **yadro o'zgarmaydi** (Open/Closed amalда). Bu — 5-10 yillik barqarorlikning asosi.
2. **API-centric** — bitta Local API barcha klient uchun (desktop/mobile/telegram/web/watch). UI-framework engine'ни buzmasдан almashtiriladi (isbot: Tauri→Flutter almashtirildi, engine tegilmади).
3. **Event-Driven yadro** — modullar bir-birini bilmaydi; hodisага obuna. Bu ChatGPT/Cursor darajasidagi tizimларда bog'lanishни kamaytirishning standart usuli.
4. **Cognitive-agent modeli** — Perceive→Plan→Act→Verify→Reflect. Chatbot emas, haqiqiy agent poydevori.
5. **Provider-agnostic hamma joyда** — LLM/Vision/Memory/Speech/EventBus — barchasi port ortида. Vendor-lock yo'q.
6. **Local-first xavfsizlik** — sirlar keychain'да, DB shifri, PII-siz loglar. Kompyuter-boshqaruv uchun to'g'ri poza.
7. **7-qatlamli xotira + Perception** — kognitiv arxitektura ("inson kabi" eslash/sezish) puxta modellangan.
8. **Hujjatlashtirish** — 12+ design hujjati, 15+ diagramma. Enterprise-daraja onboarding/barqarorlik.

---

## 3. ⚠️ Kelajakда muammo bo'lishi mumkin (halol risklar)

| # | Risk | Ta'sir | Yumshatish |
|---|------|--------|-----------|
| R1 | **Ko'lam vs bitta dasturchi** — arxitektura juda katta; over-engineering / hech qачон tugamaslik xavfi | 🔴 Yuqori | **Vertical slice** bilan yurish: har modul UCHDAN-UCHGACHA ishlaydigan kichik qism. YAGNI — Multi-agent/Vector-DB'ni haqiqiy ehtiyoj bo'lганда qur |
| R2 | **Python paketlash** (PyInstaller: dlib/opencv/whisper native deps, har OS) | 🔴 Yuqori | Eng qiyin qism; D5'да alohida spike. Alternativ: ba'zi og'ir deps'ni ixtiyoriy plugin qilish |
| R3 | **Event Bus haddan tashqari ishlatilishi** — hammasi event bo'lsa, oqimни debug/trace qiyin | 🟡 O'rta | Qat'iy qoida: event = **decoupling nuqtasi**; request/response = to'g'ridan chaqiruv. `trace_id` majburiy |
| R4 | **Memory consolidation narxi** — har suhbatда LLM chaqirish = token + latency | 🟡 O'rta | Async/batch consolidate; arzon model (Haiku); faqat "muhim" suhbat |
| R5 | **Lokal LLM tezligi** (Ollama/LMStudio M1'да sekin) | 🟡 O'rta | Kutilmani boshqarish; lokal = fallback/privat rejim, asosiy = bulut |
| R6 | **Embeddings/Vector sifati** — lokal embedding og'ir (torch), API — internet | 🟡 O'rta | M3'да qaror; kichik lokal model yoki arzon embedding-API; SQLite-cosine minglab yozuv uchun yetarli |
| R7 | **Test yuki** — enterprise sifat real test qamrovини talab qiladi | 🟡 O'rta | Har modulда **contract-test** (port↔provider) + mock; CI'да majburiy |
| R8 | **SDK/API barqarorligi** — plugin/klient paydo bo'lгандан keyin buzuvchi o'zgarish qimmat | 🟡 O'rta | Qat'iy SemVer; `/api/v1` + `min_doda`; deprecation siyosati |
| R9 | **v1.0.0 → v2 ma'lumot migratsiyasi** — mavjud xotira/yuz/eslatmalar | 🟢 Past | M3/M12'да migratsiya skripti (eski JSON/fayllar → yangi DB) |
| R10 | **Kod imzolash narxi** — notarization/sign auto-update ishonchi uchun shart | 🟢 Past | Byudjet qarori; dastlab imzosiz (ogohlantirish bilan) mumkin |

---

## 4. 💡 Tavsiyalar (arxitekturага qo'shish) — 13 dan tashqari

Bular hozir **hujjatда qayd etildi**, tegishli modulда quriladi:

1. **Provider Capabilities** — har provider nimani qo'llашини e'lon qiladi (vision? streaming? tools?) → agent moslashadi (masalan lokal model tool-calling'ни qo'llamаса). *(→ M2)*
2. **Fallback / Graceful degradation** — provider ishlamаса zanjir (Claude→OpenRouter→lokal); internet yo'qда offline rejim. *(→ M2)*
3. **Contract tests** — har port uchun umumiy test-to'plami; yangi provider avtomatik tekshiriladi. *(→ M1)*
4. **Cost/Usage tracking** — token/xarajat hisobi (`/status`, budjet-ogohlantirish). Shaxsiy agent uchun muhim. *(→ M2)*
5. **Prompt management** — system/persona promptlari **versiyalangan asset** (kodда tarqoq emas). *(→ M4)*
6. **Evaluation harness** — agent xatti-harakatini test (v1.0.0'даги coverage-test kabi). *(→ M4/M7)*
7. **Event reliability** — dead-letter + retry + backpressure (event yo'qolmasin, tizim to'lib ketmasin). *(→ M1)*
8. **Idempotency** — tool/task qayta-urinишда ikki marta bajarilmasin (`request_id`). *(→ M6/M9)*
9. **Circuit breaker** — tashqi API (LLM/weather) uzluksiz xato bersa vaqtincha to'xtatish. *(→ M2)*
10. **Feature flags** — yangi imkoniyатни xavfsiz yoq/o'chir (kod-shohsiz). *(→ M1)*

---

## 5. Verdikt

**Arxitektura professional darajaga yetdi.** 13/13 talab qamrab olindi; Event-Driven, Plugin-First,
Cognitive-Agent va Clean/SOLID tamoyillari to'liq. Kengaytma nuqtalari aniq → 5–10 yil davomida
**yadro qayta yozilmasдан** rivojlanadi.

**Asosiy shart — sifat emas, INTIZOM:** eng katta xavf (R1) texnik emas, balki ko'lam. Tavsiya:
**har modulни vertical-slice sifatida** (kichik, uchdan-uchgacha ishlaydigan, test qilinган) qurish;
YAGNI'ni saqlash (Multi-agent/Vector-DB'ni ehtiyoj tug'ilганда).

> ✅ **NATIJA: arxitektura tasdiqlashга tayyor. Modul 1 (Foundation) implementatsiyasiни boshlash mumkin** —
> R3/R7/tavsiya-1,3,7,10 (Event-intizom, contract-test, capabilities, event-reliability, feature-flags) M1'га kiritiladi.

---

### Ilova: qaror jurnali (ADR-uslub qisqacha)
- **Flutter (Tauri/Electron emas)** — foydalanuvchi Flutter-dev; bitta codebase **desktop+mobil**; native; uzoq-muddat.
- **Event Bus lokal asyncio (broker emas)** — hozir bitta jarayon; broker post-M12.
- **SQLite (Postgres emas)** — bitta qurilma; Postgres ko'p-qurilma/mini-PC'да.
- **Bitta agent (multi-agent emas)** — interfeys tayyor; qo'shiladi ehtiyoj bo'lганда.
