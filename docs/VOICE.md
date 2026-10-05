# DODA — Voice Module

DODA foydalanuvchi bilan **tabiiy o'zbek tilida ovoz orqali** suhbatlashadi. Bu hujjat ovoz
modulining arxitekturasi, provayderlari, sozlamalari va ishga tushirishni tavsiflaydi.

> Ovoz moduli **Python engine** ichida (FE'dan mustaqil). UI/dashboard `voice.*` eventlarini
> WebSocket orqali (delivery qatlami) oladi — bu qatlam alohida modul.

---

## 1. Oqim (Flow)

```
MIKROFON → VAD → STT → TEXT → DODA AGENT → CLAUDE → TEXT → TTS → KARNAY
```

- **VAD** lokal ishlaydi (`energy` default) — audio doimiy bulutga yuborilmaydi (privacy).
- **STT** faqat nutq aniqlanganda ishlaydi.
- **Agent** — bitta `CognitiveAgent` (chat va voice bir xil pipeline: recall → Claude → tools →
  reflect). Voice uchun alohida agent YO'Q.
- **TTS** javobni o'zbekcha ovozga aylantiradi (`edge-tts uz-UZ-SardorNeural` default).

Ikki rejim:
- **`VoicePipeline.listen_once()`** — sodda: wake → yozish → STT → agent → TTS → ijro.
- **`RealtimeVoiceSession.run_turn()`** — VAD-boshqariladigan, holat-mashina + **barge-in**.

---

## 2. Arxitektura

Clean Architecture — provider-specific kod core'ga kirmaydi.

| Qatlam | Joy |
|--------|-----|
| **Portlar** (domen) | `core/interfaces/voice.py` — `SpeechToText`, `StreamingSpeechToText`, `TextToSpeech`, `VoiceActivityDetector`, `AudioInput`, `StreamingAudioInput`, `AudioOutput`, `WakeWordDetector` |
| **Modellar** | `core/models/speech.py` — `VoiceState`, `SpeechResult`, `SpeechChunk`, `SpeechConfig`, `VoiceEvent` |
| **Provayderlar** | `providers/voice/{stt,tts,vad,audio,wake}/` + `registry.py` |
| **Ilova** | `voice/` — `VoicePipeline`, `RealtimeVoiceSession`, `VoiceSession` (state machine), `detect_language` |

Yangi provider = tegishli subpaketda yangi adapter + `registry` ga bitta tarmoq. **Core o'zgarmaydi.**

---

## 3. Provayderlar

| Tur | Default | Ixtiyoriy | Soxta (mock) |
|-----|---------|-----------|--------------|
| **STT** | `whisper` (CLI, o'zbek) | `elevenlabs` (Scribe) | `FakeSTT` |
| **TTS** | `edge_tts` (`uz-UZ-SardorNeural`) | `elevenlabs` | `FakeTTS` |
| **VAD** | `energy` (dep-siz, lokal) | `silero` (torch) | `FakeVAD` |
| **Audio** | OS auto (mac/linux/windows) | — | `FakeAudioInput/Output` |
| **Wake** | `KeywordWakeDetector` (STT-asosli) | openWakeWord/porcupine → v1.1 | `FakeWakeWord` |

### O'zbek tili ogohlantirishi
ElevenLabs o'zbek tilini native darajada qo'llab-quvvatlashi **kafolatlanmagan**. Shuning uchun
default STT/TTS **edge-tts + whisper**. ElevenLabs `voice.stt_provider=elevenlabs` bilan yoqiladi;
o'zbek tili tanlansa registry ogohlantirish logini chiqaradi. Sifat yetarli bo'lmasa boshqa
providerga o'ting — kod o'zgartirilmaydi.

---

## 4. Konfiguratsiya (env / `.env`)

```bash
DODA_VOICE__ENABLE_VOICE=true
DODA_VOICE__LANGUAGE=uz
DODA_VOICE__STT_PROVIDER=whisper        # whisper | elevenlabs | mock
DODA_VOICE__TTS_PROVIDER=edge_tts       # edge_tts | elevenlabs | mock
DODA_VOICE__VAD_PROVIDER=energy         # energy | silero | mock
DODA_VOICE__AUDIO_PROVIDER=auto         # auto | macos | linux | windows | mock
DODA_VOICE__TTS_VOICE=uz-UZ-SardorNeural
DODA_VOICE__VOICE_ID=                    # ElevenLabs ovoz id (agar ishlatilsa)
DODA_VOICE__WAKE_WORD=doda
DODA_VOICE__WAKE_WORD_ENABLED=false
DODA_VOICE__SAMPLE_RATE=16000
DODA_VOICE__STREAMING_ENABLED=true
DODA_VOICE__ENABLE_VAD=true
DODA_VOICE__MOCK_MODE=false             # true → barcha provayderlar soxta (kalitsiz)
```

**API kalitlari kodda EMAS** — `SecretStore` da:
- `speech.stt.key` — ElevenLabs STT kaliti
- `speech.tts.key` — ElevenLabs TTS kaliti

---

## 5. OS bo'yicha sozlash

| OS | Mikrofon | Karnay | Talab |
|----|----------|--------|-------|
| **macOS** | `ffmpeg avfoundation` | `afplay` | `brew install ffmpeg`; Mikrofon ruxsati (System Settings → Privacy) |
| **Linux** | `arecord` (ALSA) | `aplay` | `alsa-utils` |
| **Windows** | `ffmpeg dshow` | `ffplay` | `ffmpeg` PATH'da |

STT (`whisper`) va TTS (`edge-tts`) uchun: `pip install 'doda[voice]'`.

---

## 6. Mock rejim

Kalit/mikrofon bo'lmasa ham modulni ishga tushirish/test qilish:

```bash
DODA_VOICE__MOCK_MODE=true
```

Barcha provayderlar soxta (`FakeSTT`/`FakeTTS`/`FakeVAD`/`FakeAudioInput/Output`) bo'ladi.

---

## 7. Holat-mashina va barge-in

```
IDLE → LISTENING → PROCESSING → THINKING → SPEAKING → IDLE
                                              │
                        (user gapirsa) → INTERRUPTED → LISTENING
```

`RealtimeVoiceSession.interrupt()` — DODA gapirayotganda ijroni uzadi (barge-in). Noto'g'ri
o'tishlar rad etiladi (`ConfigError`).

---

## 8. Eventlar (EventBus → delivery/dashboard)

`voice.started` · `voice.state` · `voice.final_transcript` · `voice.thinking` ·
`voice.speaking` · `voice.interrupted` · `voice.completed` · `voice.error`

Dashboard bu eventlarni WebSocket orqali oladi (delivery qatlami — keyingi faza).

---

## 9. Observability (latency / metrikalar)

Har navbatda: `voice_sessions_total`, `voice_errors_total`, `stt_latency_ms`,
`agent_latency_ms`, `tts_latency_ms`, `voice_session_duration`. API kalit yoki audio kontenti
**loglanmaydi**.

---

## 10. Privacy (24/7 uy uchun)

- VAD **lokal** — audio doimiy bulutga yuborilmaydi.
- STT faqat nutq aniqlanganda ishlaydi.
- Xom audio default holatda doimiy saqlanmaydi.
- API kalitlar `SecretStore` da (0600), kodda emas.
- Mikrofon holati (`voice.state`) UI'da ko'rinadi.

---

## 11. Testlar

- Unit + **contract** testlar: STT/TTS/VAD/AudioInput/AudioOutput/WakeWord.
- Soxta provayderlar bilan (`MOCK_MODE`) — **CI'da API kalit talab qilinmaydi**.
- Real API testlari ixtiyoriy integratsiya testi (kalit bilan, lokal).

```bash
pytest doda/tests/ -q
```

---

## 12. Latency (taxminiy)

| Bosqich | Default | Realtime maslahat |
|---------|---------|-------------------|
| VAD | ~ms (lokal) | energy |
| STT | whisper: sekundlar (lokal, model hajmiga bog'liq) | streaming provider → past kechikish |
| Agent+Claude | ~1–3s | streaming javob (kelajak) |
| TTS | edge-tts: ~1s | — |

---

## 13. Kelajakdagi provayderlar (v1.1+)

- Streaming STT (ElevenLabs Scribe Realtime WebSocket) — partial/final.
- Mahalliy wake-engine (openWakeWord/porcupine).
- Streaming TTS + streaming Claude → DODA javobni to'liq kutmasdan gapira boshlaydi.
- O'zbek-native STT/TTS provayderlari (chiqqanda — registry ga bitta adapter).

Barchasi mavjud portlar ortida — **core o'zgarmaydi**.
