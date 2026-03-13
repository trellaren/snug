"""Entry-point for the snug application."""

from __future__ import annotations

import argparse
import sys

from snug.logger import DataLogger, DEFAULT_LOG_DIR, DEFAULT_FILENAME
from snug.monitor import collect, format_snapshot


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="snug",
        description=(
            "snug – cross-platform system-tray tool for monitoring, "
            "displaying and logging thermal and hardware data."
        ),
    )
    parser.add_argument(
        "--no-tray",
        action="store_true",
        help="Print a single snapshot to stdout and exit (no tray icon).",
    )
    parser.add_argument(
        "--log-dir",
        metavar="DIR",
        default=str(DEFAULT_LOG_DIR),
        help=f"Directory for log files (default: {DEFAULT_LOG_DIR}).",
    )
    parser.add_argument(
        "--log-file",
        metavar="FILE",
        default=DEFAULT_FILENAME,
        help=f"Log filename (default: {DEFAULT_FILENAME}).",
    )
    parser.add_argument(
        "--interval",
        metavar="SECONDS",
        type=float,
        default=5.0,
        help="Logging interval in seconds (default: 5).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Application entry-point.

    Returns an exit code (0 = success).
    """
    args = _parse_args(argv)

    from pathlib import Path

    log_path = Path(args.log_dir) / args.log_file
    logger = DataLogger(log_path=log_path, interval_seconds=args.interval)

    if args.no_tray:
        snapshot = collect()
        print(format_snapshot(snapshot))
        return 0

    # Lazy import so tests that don't exercise the tray don't need a display.
    try:
        from snug.tray import SnugTray
    except Exception as exc:
        print(f"Failed to initialise tray: {exc}", file=sys.stderr)
        print("Try running with --no-tray for a headless snapshot.", file=sys.stderr)
        return 1

    tray = SnugTray(logger=logger)
    tray.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
