# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Tests for the Volume Companion CLI."""

import logging
import subprocess
from pathlib import Path
import pytest

from volume_companion.cli import VolumeCLI
from volume_companion.session_state import SessionState

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
def test_do_config_outputs_state(caplog) -> None:
    """
    Lightweight integration test for the `config` command.

    Verifies that the CLI exposes current session state via logging
    without asserting on exact formatting.
    """
    cli = VolumeCLI(
        csv_path=Path("dummy.csv"),
        state=SessionState()
    )

    with caplog.at_level(logging.INFO):
        cli.do_config("")

    assert len(caplog.records) == 1
    record_message = caplog.records[0].message

    assert "bars=" in record_message
    assert "offset=" in record_message
    assert "verbose=" in record_message
