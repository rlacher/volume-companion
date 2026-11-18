# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Tests for the Volume Companion entry point."""

import io
from pathlib import Path
import subprocess
import sys

import pytest

from volume_companion.main import main

SUBPROCESS_TIMEOUT_SECONDS = 5


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


def _assert_startup_error(monkeypatch, capsys, path, message):
    """Run main with path and assert a concise startup error."""
    monkeypatch.setattr(sys, "argv", ["volume-companion", str(path)])

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert message in captured.err
    assert "Traceback" not in captured.err
    assert "Loaded CSV file" not in captured.out


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
    _assert_startup_error(
        monkeypatch, capsys, tmp_path / "missing.csv", "CSV file not found"
    )


@pytest.mark.integration
def test_main_reports_directory(monkeypatch, tmp_path, capsys):
    """A directory is reported as an invalid file, not as missing."""
    directory = tmp_path / "data"
    directory.mkdir()

    _assert_startup_error(
        monkeypatch, capsys, directory, "not a regular file"
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    "content, message",
    [
        ("", "no valid OHLCV rows"),
        (
            "2025.01.01,00:00,1,3,1,2,5\n"
            "2025.01.01,00:00,1,3,1,2,6\n",
            "Duplicate timestamp",
        ),
    ],
)
def test_main_reports_invalid_csv(
    monkeypatch, tmp_path, capsys, content, message
):
    """Invalid CSV content is reported without a traceback."""
    path = tmp_path / "invalid.csv"
    path.write_text(content, encoding="utf-8")

    _assert_startup_error(monkeypatch, capsys, path, message)


@pytest.mark.integration
def test_main_reports_unreadable_csv(monkeypatch, csv_file, capsys):
    """An unreadable CSV is reported without a traceback."""

    def deny_permission(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied", str(self))

    monkeypatch.setattr(Path, "open", deny_permission)

    _assert_startup_error(monkeypatch, capsys, csv_file, "Permission denied")


@pytest.mark.system
def test_main_reports_missing_csv_without_traceback(tmp_path):
    """The installed entry point reports a missing CSV without a traceback."""
    missing = tmp_path / "missing.csv"

    result = subprocess.run(
        ["poetry", "run", "volume-companion", str(missing)],
        input="",
        text=True,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )

    assert result.returncode == 1
    assert "CSV file not found" in result.stderr
    assert "Traceback" not in result.stderr
    assert "Loaded CSV file" not in result.stdout


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
