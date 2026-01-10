# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Tests for the Volume Companion CLI."""

import subprocess
from pathlib import Path
import pytest
from unittest.mock import Mock

from volume_companion.cli import VolumeCLI
from volume_companion.session_state import SessionState
from volume_companion.formatter import Formatter

SUBPROCESS_TIMEOUT_SECONDS = 5


@pytest.fixture
def minimal_valid_csv(tmp_path: Path) -> Path:
    """
    Create a minimal valid OHLCV CSV file suitable for system-level CLI tests.
    """
    csv_file = tmp_path / "minimal.csv"
    # Valid row: open <= high, low <= open, low <= high
    csv_file.write_text(
        "2025.01.01,00:00,1,3,1,2,5\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.fixture
def two_bar_csv(tmp_path: Path) -> Path:
    """
    Create a small valid OHLCV CSV file with two bars whose volumes are chosen
    to guarantee different scaled block heights in the ASCII output.
    """
    csv_file = tmp_path / "two_bars.csv"
    csv_file.write_text(
        "\n".join(
            [
                # High-volume bar: full blocks
                "2024.01.01,00:00,1,3,1,2,40",
                # Low-volume bar: low-level block
                "2024.01.01,00:01,1,3,1,2,5",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return csv_file


@pytest.mark.system
def test_cli_smoke(minimal_valid_csv: Path) -> None:
    """
    System-level smoke test that verifies that the tool starts via the
    Poetry entry point, accepts basic commands, responds without crashing
    and exits cleanly.
    """
    commands = "\n".join(
        [
            "config",
            "verbose",
            "quit",
        ]
    ) + "\n"

    result = subprocess.run(
        ["poetry", "run", "volume-companion", str(minimal_valid_csv)],
        input=commands,
        text=True,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )

    assert result.returncode == 0
    assert not result.stderr
    assert "bars=" in result.stdout
    assert result.stdout.count("verbose=") == 2


@pytest.mark.system
def test_cli_smoke_datetime_two_bars(two_bar_csv: Path) -> None:
    """
    System-level smoke test ensuring the CLI can load a small valid CSV file,
    set a selected datetime and render ASCII volume bars.
    """
    commands = "\n".join(
        [
            "datetime 2025-01-01T00:05",
            "quit",
        ]
    ) + "\n"

    result = subprocess.run(
        ["poetry", "run", "volume-companion", str(two_bar_csv)],
        input=commands,
        text=True,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )

    assert result.returncode == 0
    assert not result.stderr

    out = result.stdout
    print(out)

    assert "selected_datetime=" in out

    blocks = "▁▂▃▄▅▆▇█"
    non_full_blocks = blocks[:-1]   # all block levels except the full block

    present_blocks = {ch for ch in blocks if ch in out}

    assert "█" in present_blocks
    assert any(ch in present_blocks for ch in non_full_blocks)


@pytest.mark.integration
def test_do_config_outputs_state(capsys) -> None:
    """
    Lightweight integration test for the `config` command.

    Verifies that the CLI exposes current session state via logging
    without asserting on exact formatting.
    """
    mock_data_store = Mock()

    cli = VolumeCLI(
        state=SessionState(),
        formatter=Formatter(),
        data_store=mock_data_store
    )

    cli.do_config("")

    captured = capsys.readouterr()

    assert "bars=" in captured.out
    assert "offset=" in captured.out
    assert "verbose=" in captured.out
    mock_data_store.assert_not_called()
