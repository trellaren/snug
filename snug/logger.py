"""CSV-based data logger for hardware snapshots."""

from __future__ import annotations

import csv
import os
import threading
from pathlib import Path
from typing import Optional

from snug.monitor import HardwareSnapshot, collect


# Default log directory: <user home>/snug_logs/
DEFAULT_LOG_DIR = Path.home() / "snug_logs"
DEFAULT_FILENAME = "snug_data.csv"


class DataLogger:
    """Periodically collects hardware data and appends it to a CSV file.

    Parameters
    ----------
    log_path:
        Full path to the CSV file.  The parent directory is created
        automatically if it does not exist.
    interval_seconds:
        How often (in seconds) a new row is appended.
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        interval_seconds: float = 5.0,
    ) -> None:
        self.log_path: Path = (
            Path(log_path) if log_path else DEFAULT_LOG_DIR / DEFAULT_FILENAME
        )
        self.interval_seconds = interval_seconds

        self._timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._running = False
        self._fieldnames: list[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start periodic logging."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self._schedule_next()

    def stop(self) -> None:
        """Stop periodic logging."""
        with self._lock:
            self._running = False
            if self._timer is not None:
                self._timer.cancel()
                self._timer = None

    def log_snapshot(self, snapshot: Optional[HardwareSnapshot] = None) -> None:
        """Write a single snapshot row to the CSV file immediately.

        If *snapshot* is ``None``, a fresh one is collected.
        """
        if snapshot is None:
            snapshot = collect()

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        row = snapshot.to_dict()
        file_exists = self.log_path.exists() and os.path.getsize(self.log_path) > 0

        # Update known fieldnames so the CSV header stays consistent.
        for key in row:
            if key not in self._fieldnames:
                self._fieldnames.append(key)

        with open(self.log_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=self._fieldnames, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        """Called by the background timer; logs one row then re-schedules."""
        try:
            self.log_snapshot()
        finally:
            with self._lock:
                if self._running:
                    self._schedule_next()

    def _schedule_next(self) -> None:
        self._timer = threading.Timer(self.interval_seconds, self._tick)
        self._timer.daemon = True
        self._timer.start()
