# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Tests for the Volume Companion entry point."""

import io
import sys

import pytest

from volume_companion.main import main


@pytest.fixture
def csv_file(tmp_path):
    """Create a minimal valid two-bar OHLCV CSV file."""
    path = tmp_path / "sample.csv"
    path.write_text(
        "2025.01.01,00:00,1,3,1,2,5\n"
        "2025.01.01,00:01,1,3,1,2,6\n",
        encoding="utf-8",
    )
    return path


@pytest.mark.integration
def test_main_starts_cli_and_quits(monkeypatch, csv_file, capsys):
    """The entry point loads a CSV and exits cleanly on quit."""
    monkeypatch.setattr(
        sys, "argv", ["volume-companion", str(csv_file)]
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO("quit\n"))

    main()

    captured = capsys.readouterr()
    assert "Loaded CSV file sample.csv" in captured.out
    assert "with 2 bars" in captured.out
    assert "Bye." in captured.out
    assert captured.err == ""


@pytest.mark.integration
def test_main_reports_missing_csv(monkeypatch, tmp_path, capsys):
    """A missing CSV path is reported without a traceback."""
    missing = tmp_path / "missing.csv"
    monkeypatch.setattr(
        sys, "argv", ["volume-companion", str(missing)]
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "CSV file not found" in captured.err
    assert "Loaded CSV file" not in captured.out


def test_main_requires_csv_path(monkeypatch, capsys):
    """A missing positional argument exits with a usage error."""
    monkeypatch.setattr(sys, "argv", ["volume-companion"])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert "csv_path" in captured.err
    assert "Loaded CSV file" not in captured.out
