"""Hardware and thermal data collection using psutil."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import psutil


@dataclass
class TemperatureReading:
    """A single temperature sensor reading."""

    label: str
    current: float  # degrees Celsius
    high: Optional[float] = None
    critical: Optional[float] = None


@dataclass
class HardwareSnapshot:
    """A point-in-time snapshot of hardware metrics."""

    timestamp: datetime.datetime = field(
        default_factory=lambda: datetime.datetime.now()
    )
    cpu_percent: float = 0.0
    cpu_freq_mhz: Optional[float] = None
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    temperatures: Dict[str, List[TemperatureReading]] = field(
        default_factory=dict
    )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def has_temperatures(self) -> bool:
        return bool(self.temperatures)

    def flat_temperatures(self) -> List[TemperatureReading]:
        """Return all temperature readings as a flat list."""
        readings: List[TemperatureReading] = []
        for group in self.temperatures.values():
            readings.extend(group)
        return readings

    def max_temperature(self) -> Optional[float]:
        """Return the highest current temperature across all sensors."""
        readings = self.flat_temperatures()
        if not readings:
            return None
        return max(r.current for r in readings)

    def to_dict(self) -> dict:
        """Serialise the snapshot to a flat dictionary (for CSV logging)."""
        result: dict = {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": round(self.cpu_percent, 1),
            "cpu_freq_mhz": (
                round(self.cpu_freq_mhz, 1)
                if self.cpu_freq_mhz is not None
                else ""
            ),
            "memory_percent": round(self.memory_percent, 1),
            "memory_used_mb": round(self.memory_used_mb, 1),
            "memory_total_mb": round(self.memory_total_mb, 1),
            "disk_percent": round(self.disk_percent, 1),
            "disk_used_gb": round(self.disk_used_gb, 2),
            "disk_total_gb": round(self.disk_total_gb, 2),
        }

        for sensor_name, readings in self.temperatures.items():
            for reading in readings:
                col = f"temp_{sensor_name}_{reading.label}_c".lower().replace(
                    " ", "_"
                )
                result[col] = round(reading.current, 1)

        return result


def collect() -> HardwareSnapshot:
    """Collect a hardware snapshot from the local machine."""
    snapshot = HardwareSnapshot()

    # CPU
    snapshot.cpu_percent = psutil.cpu_percent(interval=None)
    freq = psutil.cpu_freq()
    if freq is not None:
        snapshot.cpu_freq_mhz = freq.current

    # Memory
    mem = psutil.virtual_memory()
    snapshot.memory_percent = mem.percent
    snapshot.memory_used_mb = mem.used / (1024 ** 2)
    snapshot.memory_total_mb = mem.total / (1024 ** 2)

    # Disk (root / first partition)
    try:
        disk = psutil.disk_usage("/")
        snapshot.disk_percent = disk.percent
        snapshot.disk_used_gb = disk.used / (1024 ** 3)
        snapshot.disk_total_gb = disk.total / (1024 ** 3)
    except (PermissionError, OSError):
        pass

    # Thermal sensors
    if hasattr(psutil, "sensors_temperatures"):
        try:
            raw = psutil.sensors_temperatures()
            if raw:
                for name, entries in raw.items():
                    snapshot.temperatures[name] = [
                        TemperatureReading(
                            label=e.label or name,
                            current=e.current,
                            high=e.high if e.high else None,
                            critical=e.critical if e.critical else None,
                        )
                        for e in entries
                    ]
        except (AttributeError, OSError):
            pass

    return snapshot


def format_snapshot(snapshot: HardwareSnapshot) -> str:
    """Return a human-readable summary of a snapshot."""
    lines = [
        f"Timestamp : {snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        f"CPU       : {snapshot.cpu_percent:.1f}%"
        + (
            f"  @ {snapshot.cpu_freq_mhz:.0f} MHz"
            if snapshot.cpu_freq_mhz
            else ""
        ),
        f"Memory    : {snapshot.memory_percent:.1f}%"
        f"  ({snapshot.memory_used_mb:.0f} / {snapshot.memory_total_mb:.0f} MB)",
        f"Disk      : {snapshot.disk_percent:.1f}%"
        f"  ({snapshot.disk_used_gb:.1f} / {snapshot.disk_total_gb:.1f} GB)",
    ]

    if snapshot.has_temperatures:
        lines.append("Temperatures:")
        for sensor, readings in snapshot.temperatures.items():
            for r in readings:
                high_str = (
                    f"  high={r.high:.0f}°C" if r.high is not None else ""
                )
                crit_str = (
                    f"  crit={r.critical:.0f}°C"
                    if r.critical is not None
                    else ""
                )
                lines.append(
                    f"  {sensor}/{r.label}: {r.current:.1f}°C{high_str}{crit_str}"
                )
    else:
        lines.append("Temperatures: (not available on this platform)")

    return "\n".join(lines)
