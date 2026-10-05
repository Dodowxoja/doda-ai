"""``ScheduledTask`` modeli testi."""

from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

from doda.core.models.task import ScheduledTask, TaskStatus


def test_defaults() -> None:
    task = ScheduledTask(id="a", prompt="ish", run_at=datetime(2026, 8, 9, 12, 0, 0))
    assert task.interval_seconds == 0.0
    assert task.status == TaskStatus.PENDING
    assert task.is_recurring is False


def test_recurring_flag() -> None:
    task = ScheduledTask(
        id="a", prompt="ish", run_at=datetime(2026, 8, 9, 12, 0, 0), interval_seconds=60.0
    )
    assert task.is_recurring is True


def test_is_frozen() -> None:
    task = ScheduledTask(id="a", prompt="ish", run_at=datetime(2026, 8, 9, 12, 0, 0))
    with pytest.raises(dataclasses.FrozenInstanceError):
        task.status = TaskStatus.DONE  # type: ignore[misc]
