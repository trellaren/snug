# snug
A cross-platform Python application with system-tray access for monitoring, displaying and logging thermal and other hardware data.

## Features

- **System-tray icon** – lives in your notification area with a clean thermometer icon.
- **Hardware monitoring** – CPU usage & frequency, memory, disk, and thermal sensor readings (via `psutil`).
- **CSV data logging** – periodically appends a timestamped row to a configurable CSV file.
- **Cross-platform** – works on Linux, macOS, and Windows.

## Requirements

- Python ≥ 3.9
- [`psutil`](https://github.com/giampaolo/psutil) ≥ 5.9
- [`pystray`](https://github.com/moses-palmer/pystray) ≥ 0.19
- [`Pillow`](https://python-pillow.org/) ≥ 10.0

Install all dependencies:

```bash
pip install psutil pystray Pillow
```

## Installation

```bash
pip install .
```

## Usage

### System-tray mode (default)

```bash
snug
```

The tray icon provides a menu to:

| Menu item | Description |
|-----------|-------------|
| **View Hardware Stats** | Opens a live-refresh window showing all metrics |
| **Logging → Start Logging** | Begins writing data to the CSV log file |
| **Logging → Stop Logging** | Stops the background logger |
| **Logging → Open Log Folder** | Opens the log directory in your file manager |
| **Quit** | Stops logging and exits |

### Headless / CI mode

Print a single snapshot and exit without opening a tray icon:

```bash
snug --no-tray
```

Sample output:

```
Timestamp : 2026-03-13 20:00:00
CPU       : 12.3%  @ 2400 MHz
Memory    : 45.6%  (7290 / 15990 MB)
Disk      : 37.4%  (53.9 / 144.3 GB)
Temperatures: (not available on this platform)
```

### Options

```
usage: snug [-h] [--no-tray] [--log-dir DIR] [--log-file FILE] [--interval SECONDS]

options:
  --no-tray            Print a single snapshot to stdout and exit.
  --log-dir DIR        Directory for log files (default: ~/snug_logs).
  --log-file FILE      Log filename (default: snug_data.csv).
  --interval SECONDS   Logging interval in seconds (default: 5).
```

## Project structure

```
snug/
├── snug/
│   ├── __init__.py
│   ├── monitor.py   # hardware / thermal data collection
│   ├── logger.py    # CSV data logger
│   ├── tray.py      # system-tray icon & menus (pystray + tkinter)
│   └── main.py      # CLI entry-point
└── tests/
    ├── test_monitor.py
    ├── test_logger.py
    └── test_main.py
```

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```
