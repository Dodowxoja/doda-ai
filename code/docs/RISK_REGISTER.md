# DODA — Risk Register

> Loyiha xavflari. **P** = Probability (ehtimol), **I** = Impact (ta'sir): 🟢 Past · 🟡 O'rta · 🔴 Yuqori.
> Har modulда tegishli risk qayta ko'rib chiqiladi.

---

## 🔧 Texnik

| ID | Risk | P | I | Yumshatish (Mitigation) |
|----|------|:-:|:-:|-------------------------|
| T1 | **Ko'lam vs bitta dasturchi** — arxitektura katta, tugamaslik xavfi | 🔴 | 🔴 | Vertical-slice; YAGNI; v1.0 = 13 feature LOCK; multi-agent/vector-DB kechiktirilган |
| T2 | Event-Bus haddan ortiq ishlatilishi — debug qiyin | 🟡 | 🟡 | Event = decoupling nuqtasi; sync = to'g'ridan; `trace_id` majburiy |
| T3 | Memory consolidation narxi/latency | 🟡 | 🟡 | Async/batch; arzon model; faqat muhim suhbat |
| T4 | Clean-Arch over-engineering (kod ko'payishi) | 🟡 | 🟡 | Faqat kerakli abstraktsiya; port = real ehtiyoj bo'lganда |

## 💰 Moliyaviy

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| F1 | **LLM token xarajati** (Claude) o'sishi | 🟡 | 🟡 | Cost-tracking (M2); arzon model (Haiku); prompt-caching; budjet-ogohlantirish |
| F2 | **Kod imzolash** — Apple $99/yr + Windows sert. | 🟡 | 🟡 | Byudjet rejа; dastlab imzosiz (ogohlantirish); release oldidan hal |
| F3 | Embedding/vision API xarajati | 🟢 | 🟡 | Lokal embedding opsiyasi; vision faqat so'ralганда |

## 🌐 API

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| A1 | LLM provider uzilishi/rate-limit | 🟡 | 🔴 | **Fallback zanjiri** (Claude→OpenRouter→lokal) + circuit-breaker |
| A2 | Provider API o'zgarishi (buzuvchi) | 🟡 | 🟡 | Provider port ortида izolyatsiya; versiya-pin; contract-test |
| A3 | Anthropic siyosat/kvota o'zgarishi | 🟢 | 🟡 | Multi-provider — vendor-lock yo'q |

## ⚡ Performance

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| P1 | Whisper/STT M1 CPU'да sekin | 🟡 | 🟡 | Online-first (Google); kichik model; thread-executor |
| P2 | Lokal LLM sekin (v2.0) | 🟡 | 🟡 | Lokal = fallback/privat; asosiy bulut |
| P3 | 24/7 xotira/CPU sizishi (long-running) | 🟡 | 🔴 | Watchdog; profiling; battery-aware; Telemetry (M14) |

## 💻 Platforma

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| PL1 | macOS ruxsatlari (camera/screen/mic/accessibility) | 🔴 | 🟡 | `ruxsatlar` tekshiruvi; aniq yo'l-yo'riq UI; per-process gotcha hujjatlanган |
| PL2 | Windows/Linux farqlari (path/service/tray) | 🟡 | 🟡 | Abstraktsiya qatlami; per-OS test; CI matrix |
| PL3 | Flutter desktop yetuklik (installer tooling) | 🟡 | 🟡 | `flutter_distributor`/`msix` sinash; erta spike |

## 📦 Packaging

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| PK1 | **Python paketlash** (PyInstaller: dlib/opencv/whisper, har OS) | 🔴 | 🔴 | Eng qiyin — D5 alohida spike; og'ir deps'ni ixtiyoriy plugin; CI matrix |
| PK2 | Binar hajmi katta | 🟡 | 🟢 | Faqat kerakli deps; lazy-import; ixtiyoriy modullar |

## 🧪 Testing

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| TS1 | Test yuki (enterprise sifat) e'tibordan chetда | 🟡 | 🔴 | DoD'да majburiy; contract-test; CI'да gate; ≥80% coverage |
| TS2 | AI xatti-harakat non-deterministik (test qiyin) | 🟡 | 🟡 | Eval-harness (M13); mock LLM; strukturали javob |

## 🚀 Deployment

| ID | Risk | P | I | Mitigation |
|----|------|:-:|:-:|-----------|
| D1 | Auto-update buzilса (bricking) | 🟢 | 🔴 | Imzolangan update; staged rollout; rollback; backup |
| D2 | Migratsiya (v1.0.0→v2) ma'lumot yo'qolishi | 🟡 | 🔴 | Migratsiya skripti + backup; test; soft-cutover |
| D3 | CI/CD sekretlari leak | 🟢 | 🔴 | GitHub Secrets; hech qачон logда; imzo kalitlari xavfsiz |

---

## Eng yuqori (🔴/🔴) — doimiy nazorat
**T1** (ko'lam), **PK1** (Python paketlash). Bular har modulда qayta baholanadi.
