# DODA — Vision

> Loyihaning "nima uchun"i. Har qaror shu vizionга xizmat qiladi.

---

## DODA nima?

DODA — **doimiy shaxsiy AI agent-platforma**. Oddiy chatbot emas: u ko'radi (kamera),
eshitadi (ovoz), eslaydi (uzoq xotira), rejalashtiradi (planning), harakat qiladi (tools) va
kompyuterni boshqaradi — desktopда, kelajakда mobil va uy-serverida. Provider-agnostic
(Claude asosiy, keyin Gemini/OpenAI/lokal), plugin bilan kengayadi.

## Nima uchun yaratilmoqda?

- **Shaxsiy, local-first AI** — ma'lumot bulutда emas, foydalanuvchi qurilmasида (maxfiylik).
- **O'zbek tili uchun** — birinchi darajali uz (+ru/en) qo'llab-quvvatlash; bozorда kam.
- **Bitta uzoq-muddatли platforma** — 5–10 yil rivojlanadigan, qayta yozilmaydigan poydevor.
- **Egasига moslashган** — foydalanuvchini biladi, loyihalarини eslaydi, qayta tushuntirish shart emas.

## Kim uchun?

- **Asosiy:** loyiha egasi (Muhammadxo'ja) — shaxsiy 24/7 yordamchi.
- **Keyin:** o'zbek-tilли foydalanuvchilar, dasturchilar (agent+tools), uy-avtomatlashtirish ishqibozlari.

## Qanday muammolarни hal qiladi?

| Muammo | DODA yechimi |
|--------|--------------|
| Kompyuterni qo'lда boshqarish sekin | Ovoz + agent bilan avtomatlashtirish |
| AI har safar kontekstni unutadi | 7-qatlamli uzuz xotira |
| Maxfiylik (bulut AI) | Local-first, sirlar keychain'да |
| O'zbek tili zaif qo'llanadi | uz birinchi darajали |
| Ko'p qurilma/ilova tarqoq | Bitta API — desktop/mobil/telegram/web |
| Vendor-lock (bitta model) | Provider-agnostic (istalgan LLM) |

## Maqsadlar (o'lchanadigan)

### 🎯 1 yil — **Professional Desktop AI Assistant**
- v1.0 desktop (Flutter) o'rnatiladigan (DMG/EXE/AppImage/DEB) release.
- Chat + Claude + 7-qatlam xotira + ovoz + vision + tools + plugin SDK + tasks.
- 24/7 background service, auto-start, auto-update.
- Enterprise sifat: test, mypy, ci/cd, hujjatlar.

### 🎯 3 yil — **Cross-platform Personal AI Platform**
- Mobil (iOS/Android — bir codebase). Multi-provider (Gemini/OpenAI/lokal).
- Multi-agent, Home AI (mini-PC 24/7), face-recognition, smart-home.
- Plugin ekotizimi (bir nechта rasmiy plugin). Cloud Sync (opt-in).

### 🎯 5 yil — **Personal AI Operating Layer**
- Uy-server + ko'p qurilma (watch/car/IoT). Robot/sensor integratsiyasi.
- Plugin Marketplace, multi-user. O'z uzbek LLM'i / voice-cloning (research).
- To'liq proaktiv agent (so'ramай foydali harakat).

---

## Asosiy tamoyillar (o'zgarmas)
**Local-first · API-centric · Provider-agnostic · Plugin-First · Event-Driven · Cognitive-Agent.**
Batafsil — [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md). Nima BO'LMAYDI — [NON_GOALS.md](NON_GOALS.md).
