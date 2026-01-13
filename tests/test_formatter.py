# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Unit tests for Formatter.format_ascii_volume."""

import re
from datetime import datetime

import pytest

from volume_companion.formatter import Formatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_ESCAPE_RE.sub("", text)


class DummyBar:
    """Minimal Bar stub for formatter tests."""

    def __init__(self, volume: float, open_: float, close: float) -> None:
        self.volume = volume
        self.open_ = open_
        self.close = close
        self.high = max(open_, close)
        self.low = min(open_, close)
        self.timestamp = datetime(2025, 1, 1, 12, 0)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bar_factory():
    """Factory fixture to create DummyBar instances."""
    def _factory(
        volume: float,
        open_: float = 1.0,
        close: float = 1.0
    ) -> DummyBar:
        return DummyBar(volume=volume, open_=open_, close=close)

    return _factory


@pytest.fixture
def bars_mixed(bar_factory) -> tuple[DummyBar]:
    """Bars with mixed volume and candle direction."""
    return [
        bar_factory(volume=10, open_=1.0, close=1.1),  # up
        bar_factory(volume=20, open_=1.1, close=1.0),  # down
        bar_factory(volume=40, open_=1.0, close=1.0),  # flat
    ]


@pytest.fixture
def bars_identical(bar_factory) -> tuple[DummyBar]:
    """Bars with identical volume."""
    return [
        bar_factory(volume=30, open_=1.0, close=1.2),
        bar_factory(volume=30, open_=1.2, close=1.0),
        bar_factory(volume=30, open_=1.0, close=1.0),
    ]


# ---------------------------------------------------------------------------
# Early-return behaviour
# ---------------------------------------------------------------------------

def test_empty_bars_returns_no_data():
    assert Formatter.format_ascii_volume([]) == "(no data)"


def test_all_zero_volume_returns_no_volume(bar_factory):
    bars = [bar_factory(volume=0), bar_factory(volume=0)]
    assert Formatter.format_ascii_volume(bars) == "(no volume)"


# ---------------------------------------------------------------------------
# Structural correctness
# ---------------------------------------------------------------------------

def test_output_has_expected_number_of_rows(bars_mixed):
    output = Formatter.format_ascii_volume(
        bars_mixed, colour_enabled=False
    )
    assert len(output.splitlines()) == Formatter._ROWS


def test_each_row_column_count_uniform_bars(bars_identical):
    output = Formatter.format_ascii_volume(
        bars_identical, colour_enabled=False
    )

    for line in output.splitlines():
        columns = line.split()
        assert len(columns) == len(bars_identical)


def test_format_verbose_single_bar_upward(bar_factory):
    bar = bar_factory(volume=10, open_=1.1, close=1.2)

    output = Formatter.format_verbose([bar])

    assert "O:1.1" in output
    assert "C:1.2" in output
    assert "Vol:10" in output
    assert "↑" in output


def test_format_verbose_multiple_bars_mixed_direction(bars_mixed):
    output = Formatter.format_verbose(bars_mixed)
    lines = output.splitlines()

    assert len(lines) == len(bars_mixed)

    assert any("↑" in line for line in lines)
    assert any("↓" in line for line in lines)

    for bar in bars_mixed:
        assert f"Vol:{int(bar.volume)}" in output


# ---------------------------------------------------------------------------
# Scaling and glyph behaviour
# ---------------------------------------------------------------------------

def test_max_volume_renders_full_block(bar_factory):
    bars = [
        bar_factory(volume=1),
        bar_factory(volume=100),
    ]

    output = Formatter.format_ascii_volume(bars, colour_enabled=False)

    bottom_row = output.splitlines()[-1]
    glyphs = bottom_row.split(" ")

    assert glyphs[1] == Formatter._BLOCKS[-1]


def test_zero_volume_renders_as_space(bar_factory):
    bars = [
        bar_factory(volume=0),
        bar_factory(volume=10),
    ]

    output = strip_ansi(
        Formatter.format_ascii_volume(bars, colour_enabled=False)
    )

    for line in output.splitlines():
        assert line[0] == " "


def test_intermediate_volume_uses_partial_block(bar_factory):
    bars = [
        bar_factory(volume=5),
        bar_factory(volume=40),
    ]

    output = strip_ansi(
        Formatter.format_ascii_volume(bars, colour_enabled=False)
    )

    glyphs = {line.split(" ")[0] for line in output.splitlines()}

    assert any(glyph in Formatter._BLOCKS[:-1] for glyph in glyphs)


# ---------------------------------------------------------------------------
# Vertical consistency
# ---------------------------------------------------------------------------

def test_no_floating_blocks(bar_factory):
    bars = [bar_factory(volume=20)]

    output = strip_ansi(
        Formatter.format_ascii_volume(bars, colour_enabled=False)
    )

    seen_block = False
    for line in output.splitlines():
        cell = line.strip()
        if cell:
            seen_block = True
        else:
            assert not seen_block


# ---------------------------------------------------------------------------
# Colour handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "colour_enabled, tty_supported, expect_ansi",
    [
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_colour_application_conditions(
    monkeypatch,
    bars_mixed,
    colour_enabled,
    tty_supported,
    expect_ansi,
):
    monkeypatch.setattr(Formatter, "supports_colour", lambda: tty_supported)

    output = Formatter.format_ascii_volume(
        bars_mixed,
        colour_enabled=colour_enabled,
    )

    assert ("\033[" in output) is expect_ansi


def test_colour_not_applied_to_empty_cells(monkeypatch, bar_factory):
    monkeypatch.setattr(Formatter, "supports_colour", lambda: True)

    bars = [bar_factory(volume=0, open_=1.0, close=1.1)]
    output = Formatter.format_ascii_volume(bars, colour_enabled=True)

    assert Formatter._GREEN not in output
    assert Formatter._RED not in output


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_output_is_deterministic(bars_mixed):
    first = Formatter.format_ascii_volume(bars_mixed, colour_enabled=False)
    second = Formatter.format_ascii_volume(bars_mixed, colour_enabled=False)

    assert first == second


# ---------------------------------------------------------------------------
# Performance sanity
# ---------------------------------------------------------------------------

def test_reasonable_large_input(bar_factory):
    bars = [bar_factory(volume=i + 1) for i in range(1_000)]

    output = Formatter.format_ascii_volume(bars, colour_enabled=False)

    assert output.count("\n") == Formatter._ROWS - 1
