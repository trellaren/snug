"""Tests for snug.monitor."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

import pytest

from snug.monitor import (
    HardwareSnapshot,
    TemperatureReading,
    collect,
    format_snapshot,
)


# ---------------------------------------------------------------------------
# HardwareSnapshot helpers
# ---------------------------------------------------------------------------


def _snapshot_with_temps() -> HardwareSnapshot:
    snap = HardwareSnapshot(
        cpu_percent=42.0,
        cpu_freq_mhz=3200.0,
        memory_percent=55.0,
        memory_used_mb=8192.0,
        memory_total_mb=16384.0,
        disk_percent=60.0,
        disk_used_gb=240.0,
        disk_total_gb=400.0,
        temperatures={
            "coretemp": [
                TemperatureReading(label="Core 0", current=65.0, high=80.0, critical=100.0),
                TemperatureReading(label="Core 1", current=67.0, high=80.0, critical=100.0),
            ]
        },
    )
    return snap


def test_has_temperatures_true():
    snap = _snapshot_with_temps()
    assert snap.has_temperatures is True


def test_has_temperatures_false():
    snap = HardwareSnapshot()
    assert snap.has_temperatures is False


def test_flat_temperatures():
    snap = _snapshot_with_temps()
    flat = snap.flat_temperatures()
    assert len(flat) == 2
    assert all(isinstance(r, TemperatureReading) for r in flat)


def test_max_temperature():
    snap = _snapshot_with_temps()
    assert snap.max_temperature() == 67.0


def test_max_temperature_empty():
    snap = HardwareSnapshot()
    assert snap.max_temperature() is None


def test_to_dict_keys():
    snap = _snapshot_with_temps()
    d = snap.to_dict()
    assert "timestamp" in d
    assert "cpu_percent" in d
    assert "memory_percent" in d
    assert "disk_percent" in d
    # Temperature columns should be present
    assert any("temp_" in k for k in d)


def test_to_dict_cpu_freq_empty_when_none():
    snap = HardwareSnapshot(cpu_freq_mhz=None)
    d = snap.to_dict()
    assert d["cpu_freq_mhz"] == ""


def test_to_dict_rounding():
    snap = HardwareSnapshot(cpu_percent=42.123456)
    d = snap.to_dict()
    assert d["cpu_percent"] == 42.1


# ---------------------------------------------------------------------------
# format_snapshot
# ---------------------------------------------------------------------------


def test_format_snapshot_contains_key_fields():
    snap = _snapshot_with_temps()
    text = format_snapshot(snap)
    assert "CPU" in text
    assert "Memory" in text
    assert "Disk" in text
    assert "65.0" in text  # temperature value


def test_format_snapshot_no_temps_message():
    snap = HardwareSnapshot()
    text = format_snapshot(snap)
    assert "not available" in text.lower()


# ---------------------------------------------------------------------------
# collect() – mock psutil calls
# ---------------------------------------------------------------------------

_FAKE_TEMPS = {
    "acpitz": [
        MagicMock(label="", current=45.0, high=None, critical=None),
    ]
}


@patch("snug.monitor.psutil.cpu_percent", return_value=30.0)
@patch("snug.monitor.psutil.cpu_freq", return_value=MagicMock(current=2400.0))
@patch(
    "snug.monitor.psutil.virtual_memory",
    return_value=MagicMock(percent=50.0, used=4 * 1024 ** 2, total=8 * 1024 ** 2),
)
@patch(
    "snug.monitor.psutil.disk_usage",
    return_value=MagicMock(percent=70.0, used=100 * 1024 ** 3, total=200 * 1024 ** 3),
)
@patch("snug.monitor.psutil.sensors_temperatures", return_value=_FAKE_TEMPS)
def test_collect_basic(mock_temps, mock_disk, mock_mem, mock_freq, mock_cpu):
    snap = collect()
    assert snap.cpu_percent == 30.0
    assert snap.cpu_freq_mhz == 2400.0
    assert snap.memory_percent == 50.0
    assert snap.disk_percent == 70.0
    assert "acpitz" in snap.temperatures


@patch("snug.monitor.psutil.cpu_percent", return_value=0.0)
@patch("snug.monitor.psutil.cpu_freq", return_value=None)
@patch(
    "snug.monitor.psutil.virtual_memory",
    return_value=MagicMock(percent=0.0, used=0, total=0),
)
@patch("snug.monitor.psutil.disk_usage", side_effect=PermissionError)
@patch("snug.monitor.psutil.sensors_temperatures", return_value={})
def test_collect_disk_permission_error(mock_temps, mock_disk, mock_mem, mock_freq, mock_cpu):
    """collect() must not raise even when disk_usage raises PermissionError."""
    snap = collect()
    assert snap.disk_percent == 0.0
    assert snap.cpu_freq_mhz is None


@patch("snug.monitor.psutil.cpu_percent", return_value=0.0)
@patch("snug.monitor.psutil.cpu_freq", return_value=None)
@patch(
    "snug.monitor.psutil.virtual_memory",
    return_value=MagicMock(percent=0.0, used=0, total=0),
)
@patch("snug.monitor.psutil.disk_usage", return_value=MagicMock(percent=0.0, used=0, total=0))
@patch("snug.monitor.psutil.sensors_temperatures", side_effect=OSError)
def test_collect_sensors_oserror(mock_temps, mock_disk, mock_mem, mock_freq, mock_cpu):
    """collect() must not raise when sensors_temperatures raises OSError."""
    snap = collect()
    assert snap.temperatures == {}
