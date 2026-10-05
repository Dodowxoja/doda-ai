"""Veb-panel (delivery qatlami) — DODA Brain/Control Center dashboardi.

Static FE: ``dashboard/index.html`` (self-contained, CSP-safe). Engine'ga WebSocket orqali
bog'lanadi (mock ↔ live bir xil interfeys). WS server (bu paketda) hali qurilmagan —
EventBus'dagi ``agent.*``/``voice.*``/``system.*`` eventlarini uzatadi. Kontrakt:
``dashboard/README.md``.
"""
