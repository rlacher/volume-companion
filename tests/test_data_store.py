# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for DataStore CSV loading."""

import datetime as dt
from pathlib import Path
import pytest

from volume_companion.data_store import DataStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def write_csv(tmp_path):
    """Write CSV lines to a file and return the path."""
    def _write_csv(filename: str, lines: list[str]) -> Path:
        path = tmp_path / filename
        path.write_text("\n".join(lines), encoding="utf-8")
        return path
    return _write_csv


@pytest.fixture
def valid_row():
    """Canonical valid OHLCV CSV row."""
    return "2024.01.01,00:00,1,3,1,2,5"


# ---------------------------------------------------------------------------
# File & Path Handling
# ---------------------------------------------------------------------------

def test_load_csv_file_not_found(tmp_path):
    missing = tmp_path / "missing.csv"
    with pytest.raises(FileNotFoundError):
        DataStore.load_csv(missing)


def test_load_csv_path_is_directory(tmp_path):
    directory = tmp_path / "dir"
    directory.mkdir()
    with pytest.raises(FileNotFoundError):
        DataStore.load_csv(directory)


# ---------------------------------------------------------------------------
# Extension Warning
# ---------------------------------------------------------------------------

def test_load_csv_non_csv_extension_warns(write_csv, capsys, valid_row):
    path = write_csv("data.txt", [valid_row])
    # Will fail because extension is wrong → warning printed
    DataStore.load_csv(path)

    output = capsys.readouterr().out
    assert "Loading file without CSV extension" in output


# ---------------------------------------------------------------------------
# Row Structure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "row",
    [
        "2024.01.01,00:00,1,2,3,4",        # 6 columns
        "2024.01.01,00:00,1,2,3,4,5,6",    # 8 columns
    ],
)
def test_load_csv_wrong_column_count(write_csv, capsys, row):
    path = write_csv("bad.csv", [row])

    with pytest.raises(ValueError):
        DataStore.load_csv(path)

    output = capsys.readouterr().out
    assert "expected 7 columns" in output


# ---------------------------------------------------------------------------
# Timestamp Parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "row",
    [
        "2024.02.30,00:00,1,2,3,4,5",  # invalid date
        "2024.01.01,25:00,1,2,3,4,5",  # invalid time
        "2024-01-01,00:00,1,2,3,4,5",  # wrong format
    ],
)
def test_load_csv_invalid_timestamp(write_csv, capsys, row):
    path = write_csv("bad_ts.csv", [row])

    with pytest.raises(ValueError):
        DataStore.load_csv(path)

    output = capsys.readouterr().out
    assert "Skipping CSV row 1" in output


# ---------------------------------------------------------------------------
# OHLCV Parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "row",
    [
        "2024.01.01,00:00,abc,2,3,4,5",  # invalid open
        "2024.01.01,00:00,1,2,3,4,xyz",  # invalid volume
        "2024.01.01,00:00, ,2,3,4,5",    # whitespace-only
    ],
)
def test_load_csv_invalid_float(write_csv, capsys, row):
    path = write_csv("bad_float.csv", [row])

    with pytest.raises(ValueError):
        DataStore.load_csv(path)

    output = capsys.readouterr().out
    assert "Skipping CSV row 1" in output


def test_load_csv_valid_scientific_notation(write_csv):
    row = "2024.01.01,00:00,1e0,3e0,1e0,2e0,5e0"
    path = write_csv("sci.csv", [row])

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 1
    bar = ds._bars[0]
    assert bar.open_ == 1.0
    assert bar.volume == 5.0


def test_load_csv_numeric_fields_with_whitespace(write_csv):
    row = "2024.01.01,00:00, 1 , 3 , 1 , 2 , 5 "
    path = write_csv("ws_numeric.csv", [row])

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 1
    bar = ds._bars[0]
    assert bar.open_ == 1.0
    assert bar.high == 3.0


# ---------------------------------------------------------------------------
# Valid Row Loading
# ---------------------------------------------------------------------------

def test_load_csv_single_valid_row(write_csv, valid_row):
    path = write_csv("one.csv", [valid_row])

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 1

    bar = ds._bars[0]
    assert bar.timestamp == dt.datetime(2024, 1, 1, 0, 0)
    assert bar.open_ == 1.0
    assert bar.high == 3.0
    assert bar.low == 1.0
    assert bar.close == 2.0
    assert bar.volume == 5.0


def test_load_csv_multiple_rows_sorted(write_csv):
    rows = [
        "2024.01.02,00:00,1,3,1,2,5",
        "2024.01.01,00:00,1,3,1,2,5",
    ]
    path = write_csv("multi.csv", rows)

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 2
    assert ds._bars[0].timestamp < ds._bars[1].timestamp


# ---------------------------------------------------------------------------
# Mixed Valid / Invalid Rows
# ---------------------------------------------------------------------------

def test_load_csv_mixed_rows(write_csv, capsys, valid_row):
    rows = [
        valid_row,
        "2024.01.01,00:00,abc,3,1,2,5",  # invalid
        valid_row,
    ]
    path = write_csv("mixed.csv", rows)

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 2

    output = capsys.readouterr().out
    assert "Skipped 1 malformed CSV rows" in output


# ---------------------------------------------------------------------------
# All Rows Invalid
# ---------------------------------------------------------------------------

def test_load_csv_all_invalid(write_csv):
    rows = [
        "2024.01.01,00:00,abc,2,3,4,5",
        "2024.01.01,00:00,abc,2,3,4,5",
    ]
    path = write_csv("all_bad.csv", rows)

    with pytest.raises(ValueError, match="no valid OHLCV rows"):
        DataStore.load_csv(path)


# ---------------------------------------------------------------------------
# Header Row Handling
# ---------------------------------------------------------------------------

def test_load_csv_header_row_is_skipped(write_csv, capsys, valid_row):
    rows = [
        "date,time,open,high,low,close,volume",
        valid_row,
    ]
    path = write_csv("header.csv", rows)

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 1

    output = capsys.readouterr().out
    assert "Skipping CSV row 1" in output


# ---------------------------------------------------------------------------
# Duplicate Timestamps
# ---------------------------------------------------------------------------

def test_load_csv_duplicate_timestamps(write_csv):
    rows = [
        "2024.01.01,00:00,1,3,1,2,5",
        "2024.01.01,00:00,6,9,7,8,10",
    ]
    path = write_csv("dup.csv", rows)

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 2
    assert ds._bars[0].open_ == 1.0
    assert ds._bars[1].open_ == 6.0


# ---------------------------------------------------------------------------
# UTF‑8 BOM Handling
# ---------------------------------------------------------------------------

def test_load_csv_utf8_bom(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_text("\ufeff2024.01.01,00:00,1,3,1,2,5", encoding="utf-8")

    ds = DataStore.load_csv(path)
    assert ds.bar_count == 1
