"""Tests for snug.logger."""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pytest

from snug.logger import DataLogger
from snug.monitor import HardwareSnapshot, TemperatureReading


def _simple_snapshot() -> HardwareSnapshot:
    return HardwareSnapshot(
        cpu_percent=25.0,
        cpu_freq_mhz=2000.0,
        memory_percent=40.0,
        memory_used_mb=4096.0,
        memory_total_mb=10240.0,
        disk_percent=50.0,
        disk_used_gb=100.0,
        disk_total_gb=200.0,
    )


def test_log_snapshot_creates_file(tmp_path):
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    snap = _simple_snapshot()
    logger.log_snapshot(snap)

    assert log_path.exists()


def test_log_snapshot_header_and_row(tmp_path):
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    snap = _simple_snapshot()
    logger.log_snapshot(snap)

    with open(log_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert len(rows) == 1
    row = rows[0]
    assert "timestamp" in row
    assert "cpu_percent" in row
    assert row["cpu_percent"] == "25.0"
    assert row["memory_percent"] == "40.0"


def test_log_snapshot_appends_rows(tmp_path):
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    logger.log_snapshot(_simple_snapshot())
    logger.log_snapshot(_simple_snapshot())

    with open(log_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert len(rows) == 2


def test_log_snapshot_with_temperatures(tmp_path):
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    snap = _simple_snapshot()
    snap.temperatures = {
        "coretemp": [TemperatureReading(label="Core 0", current=72.5)]
    }
    logger.log_snapshot(snap)

    with open(log_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    assert len(rows) == 1
    temp_cols = [k for k in rows[0] if "temp_" in k]
    assert temp_cols, "Expected at least one temperature column"
    assert rows[0][temp_cols[0]] == "72.5"


def test_log_snapshot_creates_parent_dirs(tmp_path):
    log_path = tmp_path / "nested" / "dirs" / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    logger.log_snapshot(_simple_snapshot())
    assert log_path.exists()


def test_start_stop(tmp_path):
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path, interval_seconds=0.05)
    assert not logger.is_running

    logger.start()
    assert logger.is_running

    # Let it run for a moment so at least one row should be written.
    time.sleep(0.2)
    logger.stop()
    assert not logger.is_running

    if log_path.exists():
        with open(log_path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) >= 1


def test_start_idempotent(tmp_path):
    """Calling start() twice should not raise or create duplicate timers."""
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path, interval_seconds=60)
    logger.start()
    logger.start()  # should be a no-op
    assert logger.is_running
    logger.stop()


def test_stop_when_not_running(tmp_path):
    """Calling stop() on a not-started logger should not raise."""
    log_path = tmp_path / "snug_data.csv"
    logger = DataLogger(log_path=log_path)
    logger.stop()  # should not raise
