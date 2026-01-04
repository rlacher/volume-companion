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


@pytest.mark.system
def test_cli_smoke(tmp_path: Path) -> None:
    """
    System-level smoke test for the Volume Companion CLI.

    Verifies that the tool starts via the Poetry entry point, accepts basic
    commands, responds without crashing and exits cleanly.
    """
    csv = tmp_path / "data.csv"
    csv.write_text("2025.12.30,23:00,1.17449,1.17489,1.17447,1.17455,897\n")

    commands = "\n".join(
        [
            "config",
            "verbose",
            "quit",
        ]
    ) + "\n"

    result = subprocess.run(
        ["poetry", "run", "volume-companion", str(csv)],
        input=commands,
        text=True,
        capture_output=True,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )

    assert result.returncode == 0
    assert not result.stderr
    assert "bars=" in result.stdout
    assert result.stdout.count("verbose=") == 2


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
