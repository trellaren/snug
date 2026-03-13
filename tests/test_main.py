"""Tests for snug.main CLI entry-point."""

from __future__ import annotations

from snug.main import main


def test_no_tray_prints_snapshot(capsys):
    rc = main(["--no-tray"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "CPU" in captured.out
    assert "Memory" in captured.out


def test_no_tray_custom_log_dir(tmp_path, capsys):
    rc = main(["--no-tray", "--log-dir", str(tmp_path)])
    assert rc == 0
