# DODA — Web Dashboard (Brain / Control Center)

DODA AI Agent OS'ning **Brain / Control Center** dashboardi. Bitta self-contained
`index.html` (tashqi CDN/skript/font YO'Q — CSP-safe). Dark-mode, glassmorphism, canvas
Brain Visualizer, real-time Thinking Log, sparkline metrikalar.

> **FE mustaqil.** Dashboard Python engine'ga faqat **WebSocket** orqali bog'lanadi. Mock va
> real ma'lumot **bir xil interfeys** (`bus`) orqali render qilinadi — engine tayyor bo'lganda
> bitta URL o'zgaradi, UI qayta yozilmaydi.

## Ishga tushirish

Dashboard `DODA_WS_URL` (default `ws://127.0.0.1:8765/ws`) ga ulanadi va **avtomatik
fallback** qiladi: engine ishlamasa (yoki claude.ai preview'da), `MockSource` demo eventlar
bilan to'liq ishlayveradi. Ulanish belgisi (footer'da) `● WebSocket live` / `● Mock data`
ko'rsatadi.

- **Live (haqiqiy engine) — bitta buyruq:**
  ```bash
  python -m doda.interfaces.api      # dashboard + WebSocket + HTTP — bitta portda (8765)
  ```
  So'ng brauzerda **http://127.0.0.1:8765/** ni oching. Server bir xil portda: `/` va statik
  fayllar → dashboard, `/ws` → WebSocket (real-time), `/health`·`/status` → JSON. Dashboard
  o'sha origin'ga (`ws://…/ws`) avtomatik ulanadi. Delivery qatlami (`doda/interfaces/api/`)
  engine EventBus'idagi `agent.*`/`voice.*`/`plan.*`/`task.*`/`system.metrics` eventlarini
  `{event, data}` JSON sifatida push qiladi; command bar'dan yuborilgan `{"type":"chat",...}`
  Agentga boradi. Real system-metrikalar uchun: `pip install psutil` (ixtiyoriy).
- **Preview (mock):** `index.html` ni to'g'ridan-to'g'ri oching yoki Artifact havolasidan ko'ring.

## WebSocket event kontrakti

Har xabar: `{"event": "<name>", "data": { ... }}`. Dashboard tinglaydigan eventlar
(DODA engine EventBus'idagi nomlar bilan mos):

| Event | `data` (misol) | UI ta'siri |
|-------|----------------|------------|
| `agent.thinking` | `{time, icon, msg, tag?, tint?}` | Thinking Log'ga qator (slide-in) |
| `memory.search` / `memory.saved` | `{time, msg}` | Log + Recent Events |
| `agent.tool_started` / `agent.tool_completed` | `{name, ...}` | Active Tools / log |
| `task.completed` | `{...}` | Recent Events |
| `module.status` | `{module, status: active\|idle\|error, activity}` | Brain Visualizer moduli |
| `system.metrics` | `{cpu, ram, disk, net, ramUsed, ramTotal, ...}` | Performance sparklinelar |
| `vision.frame` | `{...}` | Vision paneli |
| `voice.started/stopped/...` | `{...}` | Voice paneli |
| `scheduler.triggered` | `{...}` | Scheduler |
| `connection.lost` | `{}` | Ulanish belgisi → mock |

## Brain Visualizer — data-driven

Modullar `modules` massividan render qilinadi (`{name, icon, status, activity, usage,
errors, connections}`). **Yangi modul qo'shish** = massivga bitta obyekt + engine'dan
`module.status` eventi; frontend qayta yozilmaydi.

## Reusable komponentlar (script ichida)

`StatCard` · `ThinkingTimeline` · `BrainVisualizer` · `Sparkline` (PerformanceChart) ·
`MemoryChart` (donut) · `ToolCard` · `EventList` · `SchedulerCard` · `StatusBadge` ·
`CommandBar` — barchasi `bus` (DataSource interfeysi) orqali ma'lumot oladi.

## Xavfsizlik

**Thinking Log** faqat DODA yaratgan **user-facing** faoliyatni ko'rsatadi ("Memory searched",
"Planning next action", "Tool completed"). Claude'ning ichki chain-of-thought'i **hech qachon**
ko'rsatilmaydi (ADR bo'yicha).

## Responsive

Desktop (sidebar + 3-ustun) → Tablet (sidebar ikonka, 2-ustun) → Mobile (drawer, vertikal
stack). Brain Visualizer barcha o'lchamlarda canvas orqali moslashadi. `prefers-reduced-motion`
hurmat qilinadi.
