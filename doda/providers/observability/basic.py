"""``BasicObservability`` — Observability portining oddiy, o'rnatilgan implementatsiyasi.

- **Logging:** stdlib ``logging`` orqali strukturali (maydonlar JSON sifatida qo'shiladi).
- **Metrics:** xotiradagi hisoblagichlar (``snapshot()`` bilan o'qiladi; keyin ``/status``ga).
- **Tracing:** ``span()`` — kontekst-menejer, davomiylikni o'lchaydi va ``trace_id`` beradi.

Sir/PII yozilmasligi CHAQIRUVCHINING mas'uliyati (bu yer faqat berilganini yozadi).
Kelajakda OpenTelemetry eksporti shu implementatsiyani almashtiradi — port o'zgarmaydi.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any
from uuid import uuid4

_LEVELS: dict[str, int] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class BasicObservability:
    """Log/metrika/span'ning yengil, sinovga qulay implementatsiyasi."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """
        Args:
            logger: Ishlatiladigan logger; berilmasa ``"doda"`` nomli logger olinadi.
        """
        self._logger = logger or logging.getLogger("doda")
        self._metrics: dict[str, float] = {}

    def log(self, level: str, message: str, /, **fields: Any) -> None:
        """Strukturali log yozadi (maydonlar xabar oxiriga JSON bo'lib qo'shiladi)."""
        levelno = _LEVELS.get(level.lower(), logging.INFO)
        if fields:
            suffix = json.dumps(fields, ensure_ascii=False, default=str, sort_keys=True)
            self._logger.log(levelno, "%s | %s", message, suffix)
        else:
            self._logger.log(levelno, "%s", message)

    def metric(self, name: str, value: float = 1.0, /, **tags: str) -> None:
        """Metrikani (nom + teglar bo'yicha) yig'ib boradi."""
        key = name
        if tags:
            key += "{" + ",".join(f"{k}={tags[k]}" for k in sorted(tags)) + "}"
        self._metrics[key] = self._metrics.get(key, 0.0) + value

    @contextmanager
    def span(self, name: str, *, trace_id: str | None = None) -> Iterator[str]:
        """Bajarilish oralig'ini o'lchaydi; ``trace_id`` beradi (yo'q bo'lsa yaratadi)."""
        tid = trace_id or uuid4().hex
        start = perf_counter()
        self.log("debug", f"span.start {name}", trace_id=tid)
        try:
            yield tid
        finally:
            ms = (perf_counter() - start) * 1000.0
            self.metric(f"span.{name}.ms", ms)
            self.log("debug", f"span.end {name}", trace_id=tid, ms=round(ms, 2))

    def snapshot(self) -> dict[str, float]:
        """Joriy metrikalarning nusxasi (o'qish uchun; masalan ``/status``)."""
        return dict(self._metrics)
