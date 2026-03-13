"""System-tray interface for snug using pystray and Pillow."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import pystray
from PIL import Image, ImageDraw

from snug.logger import DataLogger
from snug.monitor import collect, format_snapshot

_ICON_SIZE = 64
_THERMOMETER_COLOR = (220, 50, 50)   # red
_BG_COLOR = (30, 30, 30)             # dark background


def _make_icon_image() -> Image.Image:
    """Draw a simple thermometer icon with Pillow."""
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = _ICON_SIZE // 2
    # Bulb at the bottom
    bulb_r = 10
    bulb_cy = _ICON_SIZE - bulb_r - 4
    draw.ellipse(
        [cx - bulb_r, bulb_cy - bulb_r, cx + bulb_r, bulb_cy + bulb_r],
        fill=_THERMOMETER_COLOR,
    )
    # Stem above the bulb
    stem_w = 6
    stem_top = 8
    stem_bot = bulb_cy - bulb_r + 2
    draw.rectangle(
        [cx - stem_w // 2, stem_top, cx + stem_w // 2, stem_bot],
        fill=_THERMOMETER_COLOR,
    )
    # White inner channel
    inner_w = 2
    draw.rectangle(
        [cx - inner_w // 2, stem_top + 4, cx + inner_w // 2, stem_bot - 2],
        fill=(255, 255, 255, 180),
    )
    return img


class SnugTray:
    """Manages the system-tray icon and menus.

    Parameters
    ----------
    logger:
        A :class:`~snug.logger.DataLogger` instance shared with the caller.
    """

    def __init__(self, logger: DataLogger) -> None:
        self._logger = logger
        self._icon: Optional[pystray.Icon] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Create and run the system-tray icon (blocking)."""
        icon_image = _make_icon_image()
        self._icon = pystray.Icon(
            name="snug",
            icon=icon_image,
            title="snug – Thermal Monitor",
            menu=self._build_menu(),
        )
        self._icon.run()

    def stop(self) -> None:
        """Stop the tray icon."""
        if self._icon is not None:
            self._icon.stop()

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem("View Hardware Stats", self._on_view_stats, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Logging",
                pystray.Menu(
                    pystray.MenuItem(
                        "Start Logging",
                        self._on_start_logging,
                        enabled=lambda _: not self._logger.is_running,
                    ),
                    pystray.MenuItem(
                        "Stop Logging",
                        self._on_stop_logging,
                        enabled=lambda _: self._logger.is_running,
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Open Log Folder", self._on_open_log_folder),
                ),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit),
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_view_stats(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        threading.Thread(target=self._show_stats_window, daemon=True).start()

    def _show_stats_window(self) -> None:
        snapshot = collect()
        text = format_snapshot(snapshot)

        root = tk.Tk()
        root.title("snug – Hardware Stats")
        root.resizable(False, False)

        frame = tk.Frame(root, padx=16, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            frame,
            text=text,
            font=("Courier", 11),
            justify=tk.LEFT,
            anchor="w",
        )
        label.pack(fill=tk.BOTH, expand=True)

        btn = tk.Button(frame, text="Refresh", command=lambda: self._refresh_label(label))
        btn.pack(pady=(8, 0))

        close_btn = tk.Button(frame, text="Close", command=root.destroy)
        close_btn.pack(pady=(4, 0))

        root.mainloop()

    def _refresh_label(self, label: tk.Label) -> None:
        snapshot = collect()
        label.config(text=format_snapshot(snapshot))

    def _on_start_logging(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._logger.start()
        log_dir = str(self._logger.log_path.parent)
        truncated = (
            log_dir if len(log_dir) <= 60 else "..." + log_dir[-57:]
        )
        self._notify(f"Logging started\nSaving to: {truncated}")

    def _on_stop_logging(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._logger.stop()
        self._notify("Logging stopped")

    def _on_open_log_folder(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        import subprocess
        import sys

        folder = str(self._logger.log_path.parent)
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", folder])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["explorer", folder])
        else:
            subprocess.Popen(["xdg-open", folder])

    def _on_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        self._logger.stop()
        icon.stop()

    def _notify(self, message: str) -> None:
        """Show a small informational popup (non-blocking)."""
        def _show() -> None:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("snug", message, parent=root)
            root.destroy()

        threading.Thread(target=_show, daemon=True).start()
