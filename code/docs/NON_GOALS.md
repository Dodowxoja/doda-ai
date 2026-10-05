# DODA v1.0 — Non-Goals (Scope Guard)

> **v1.0'да ATAYLAB YO'Q.** Bu — scope creep'дан himoya. Quyidagilar keyingi versiyaларга
> qoldirilган. Ular arxitektura darajасида **ko'zда tutilган** (port/plugin tayyor), lekin
> v1.0'да **QURILMAYDI**. "Bu v1.0'га kiradimi?" — javob shu yerда bo'lса, YO'Q.

---

| # | v1.0'да YO'Q | Nega qoldirildi | Qaysi versiyада |
|---|--------------|-----------------|-----------------|
| 1 | **Multi-User** | v1.0 bitta ega uchun; DB `user_id` tayyor, lekin UI/izolyatsiya keyin | v3.0 |
| 2 | **Face Recognition** | Lokal lib og'ir (dlib); v1.0 fokus emas | v2.0 |
| 3 | **Robot / IoT control** | Apparat integratsiyasi; katta alohida sohа | v3.0 |
| 4 | **Smart Home** | Home Assistant plugin; v1.0 core emas | v2.0 |
| 5 | **Cloud Sync** | E2E-shifr + konflikt-hал murakkab; local-first yetarli | v2.0 |
| 6 | **Local LLM (jonli)** | Ollama/LMStudio provider stub tayyor, jonli integratsiya keyin | v2.0 |
| 7 | **Plugin Marketplace** | Imzolangan katalog + moderatsiya; SDK avval barqarorlashsin | v3.0 |
| 8 | **Mobile App** | Flutter codebase tayyor bo'ladi, lekin mobil target v1.2 | v1.2 |
| 9 | **Multi-Agent (jonli)** | Orchestrator interfeysi tayyor, ko'p-agent keyin | v2.0 |
| 10 | **Telegram (yangi platformада)** | Eski v1.0.0'да ishlaydi; yangi'да plugin sifatida | v1.1 |
| 11 | **Wear OS / Watch / CarPlay / Auto** | Yangi klientlar; API tayyor, UI keyin | v3.0 |
| 12 | **O'z Uzbek LLM / voice-cloning** | Kuchli GPU/Mac kerak; research | v2.0+ |
| 13 | **API Platform (3rd-party)** | Ichki API avval barqarorlashsin | v3.0 |

---

## Muhim eslatma
- Bu ro'yxat **arxitekturани cheklamaydi** — hammasi kelajакда **yangi modul/plugin/provider/klient**
  sifatida qo'shiladi, yadro o'zgarmасдан. Bugun **QURILMAYDI**, xolos.
- **Eski v1.0.0** (flat) da bulardan ba'zilari (face-recognition, telegram) bor — u ishlab turadi.
  Yangi `doda/` platforма v1.0'да ular YO'Q (toza, fokusланган MVP).
- Agar biror talab shu ro'yxatда bo'lса — u **v1.0 blokeri EMAS**; keyingi versiyага yoziladi.

> Qoida: **v1.0 = 13 feature (PRD), boshqa hech narsa.** Yangi g'oya → [VERSION_PLAN.md](VERSION_PLAN.md)ga qo'shiladi, v1.0'га EMAS.
