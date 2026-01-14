# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Tests for the Volume Companion CLI."""

import subprocess
from datetime import datetime
from pathlib import Path
import pytest
from unittest.mock import Mock, call

from volume_companion.bar import Bar
from volume_companion.cli import VolumeCLI
from volume_companion.session_state import SessionState
from volume_companion.formatter import Formatter

SUBPROCESS_TIMEOUT_SECONDS = 5


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


@pytest.fixture
def state():
    """Mocked SessionState with realistic defaults."""
    mock_state = Mock()
    mock_state.selected_datetime = "2025-01-01T10:00"
    mock_state.as_server_datetime = datetime(2025, 1, 1, 10, 0)
    mock_state.bars = 3
    return mock_state


@pytest.fixture
def data_store():
    """Mocked DataStore."""
    return Mock()


@pytest.fixture
def formatter():
    """Mocked Formatter."""
    return Mock()


@pytest.fixture
def cli(state, formatter, data_store):
    """CLI instance under test."""
    return VolumeCLI(state=state, formatter=formatter, data_store=data_store)


@pytest.fixture
def make_bar():
    """Factory for creating realistic Bar objects with datetime timestamps."""
    def _make(ts=None):
        bar = Mock(spec=Bar)
        bar.timestamp = ts or datetime(2025, 1, 1, 10, 0)
        return bar
    return _make


# ---------------------------------------------------------------------------
# System-level smoke tests
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Integration tests for do_config
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Unit tests for _step method
# ---------------------------------------------------------------------------

def test_step_no_selected_datetime(cli, state, data_store, capsys):
    """If no datetime is selected, _step must return empty and not
    call next_slice."""
    state.selected_datetime = None

    result = cli._step(1)

    assert result == ()
    assert "No valid datetime selected" in capsys.readouterr().out
    data_store.next_slice.assert_not_called()
    state.set_from_server_datetime.assert_not_called()


def test_step_success_updates_state(cli, state, data_store, make_bar, capsys):
    """When next_slice returns bars, state must update to the last bar
    timestamp."""
    b1 = make_bar(datetime(2025, 1, 1, 10, 1))
    b2 = make_bar(datetime(2025, 1, 1, 10, 2))
    data_store.next_slice.return_value = (b1, b2)

    result = cli._step(2)

    assert result == (b1, b2)
    state.set_from_server_datetime.assert_called_once_with(
        datetime(2025, 1, 1, 10, 2)
    )
    assert "selected_datetime" in capsys.readouterr().out


def test_step_no_bars_state_unchanged(cli, state, data_store, capsys):
    """If next_slice returns empty, state must not change."""
    data_store.next_slice.return_value = ()

    result = cli._step(5)

    assert result == ()
    state.set_from_server_datetime.assert_not_called()
    assert "Step exceeds available bars" in capsys.readouterr().out


def test_step_single_bar_updates_state(cli, state, data_store, make_bar):
    """Single-bar slices must still update state correctly."""
    ts = datetime(2025, 1, 1, 10, 5)
    bar = make_bar(ts)
    data_store.next_slice.return_value = (bar,)

    result = cli._step(1)

    assert result == (bar,)
    state.set_from_server_datetime.assert_called_once_with(ts)


def test_step_passes_correct_arguments(cli, state, data_store, make_bar):
    """_step must pass correct parameters to next_slice."""
    bar = make_bar()
    data_store.next_slice.return_value = (bar,)

    cli._step(3)

    data_store.next_slice.assert_called_once_with(
        state.as_server_datetime,
        3,
        state.bars,
    )


def test_step_two_consecutive_updates(cli, state, data_store, make_bar):
    """Sequential steps must update state predictably."""
    ts1 = datetime(2025, 1, 1, 10, 1)
    ts2 = datetime(2025, 1, 1, 10, 2)

    data_store.next_slice.side_effect = [
        (make_bar(ts1),),
        (make_bar(ts2),),
    ]

    cli._step(1)
    cli._step(1)

    assert state.set_from_server_datetime.call_args_list == [
        call(ts1),
        call(ts2),
    ]


# ---------------------------------------------------------------------------
# Unit tests for _query_datetime method
# ---------------------------------------------------------------------------

def test_query_datetime_no_selection(cli, state, data_store, capsys):
    """Return empty and print error when no datetime is selected."""
    state.selected_datetime = None

    result = cli._query_datetime()

    assert result == ()
    assert "No valid datetime selected" in capsys.readouterr().out
    data_store.get_slice.assert_not_called()
    state.set_from_server_datetime.assert_not_called()


def test_query_datetime_empty_slice(cli, state, data_store, capsys):
    """Return empty and print message when slice is empty."""
    data_store.get_slice.return_value = ()

    result = cli._query_datetime()

    assert result == ()
    output = capsys.readouterr().out
    assert "before the first available bar" in output
    state.set_from_server_datetime.assert_not_called()


def test_query_datetime_exact_match(
        cli, state, data_store, make_bar, capsys
):
    """Update state and print selected datetime when last bar matches
    server_dt."""
    ts = state.as_server_datetime
    bars = (make_bar(ts), make_bar(ts), make_bar(ts))
    data_store.get_slice.return_value = bars

    result = cli._query_datetime()

    assert result == bars
    state.set_from_server_datetime.assert_called_once_with(ts)

    output = capsys.readouterr().out
    assert "selected_datetime=" in output
    assert "No bar exactly" not in output
    assert "Only" not in output


def test_query_datetime_no_exact_match(
        cli, state, data_store, make_bar, capsys
):
    """Warn when no bar exactly matches the selected datetime."""
    bars = (
        make_bar(datetime(2025, 1, 1, 9, 58)),
        make_bar(datetime(2025, 1, 1, 9, 59)),
        make_bar(datetime(2025, 1, 1, 9, 59, 30)),  # not equal to server_dt
    )
    data_store.get_slice.return_value = bars

    cli._query_datetime()

    output = capsys.readouterr().out
    assert "No bar exactly at" in output
    state.set_from_server_datetime.assert_called_once_with(bars[-1].timestamp)


def test_query_datetime_fewer_bars_than_requested(
        cli, state, data_store, make_bar, capsys
):
    """Warn when fewer bars than requested are available."""
    state.bars = 5
    bars = (
        make_bar(datetime(2025, 1, 1, 9, 58)),
        make_bar(datetime(2025, 1, 1, 9, 59)),
    )
    data_store.get_slice.return_value = bars

    result = cli._query_datetime()

    assert result == bars
    output = capsys.readouterr().out
    assert "Only 2 bars available" in output
    state.set_from_server_datetime.assert_called_once_with(bars[-1].timestamp)
