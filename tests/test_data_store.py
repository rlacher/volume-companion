# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for DataStore: CSV loading and time-series slicing."""

import datetime as dt
from pathlib import Path
import pytest

from volume_companion.data_store import DataStore
from volume_companion.bar import Bar


# ============================================================================
# Fixtures
# ============================================================================

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


@pytest.fixture
def make_bar():
    """Factory fixture to create a Bar with a timestamp string."""
    def _make_bar(ts: str, price: float = 100.0, volume: float = 1.0):
        return Bar(
            timestamp=dt.datetime.strptime(ts, "%Y-%m-%d %H:%M"),
            open_=price,
            high=price,
            low=price,
            close=price,
            volume=volume,
        )
    return _make_bar


@pytest.fixture
def make_store(make_bar):
    """Factory fixture to create a DataStore from timestamp strings."""
    def _make_store(timestamps):
        bars = [make_bar(ts) for ts in timestamps]
        return DataStore(bars)
    return _make_store


# ============================================================================
# Tests for DataStore.load_csv
# ============================================================================

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


# ============================================================================
# Tests for DataStore.get_slice
# ============================================================================

# ---------------------------------------------------------------------------
# Functional correctness
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "timestamps,end_dt,n,expected_minutes",
    [
        (
            ["2024-01-01 10:00", "2024-01-01 10:01", "2024-01-01 10:02"],
            dt.datetime(2024, 1, 1, 10, 2),
            2,
            [1, 2],
        ),
        (
            ["2024-01-01 10:00", "2024-01-01 10:02"],
            dt.datetime(2024, 1, 1, 10, 1),
            5,
            [0],
        ),
    ],
)
def test_get_slice_basic_valid(
    make_store, timestamps, end_dt, n, expected_minutes
):
    store = make_store(timestamps)
    result = store.get_slice(end_dt, n)
    assert [b.timestamp.minute for b in result] == expected_minutes


def test_get_slice_n_equals_one_exact_match(make_store):
    store = make_store(["2024-01-01 10:00", "2024-01-01 10:01"])
    end_dt = dt.datetime(2024, 1, 1, 10, 1)
    result = store.get_slice(end_dt, 1)
    assert [b.timestamp.minute for b in result] == [1]


# ---------------------------------------------------------------------------
# Time-boundary conditions
# ---------------------------------------------------------------------------

def test_get_slice_end_dt_before_first_bar(make_store):
    store = make_store(["2024-01-01 10:00"])
    end_dt = dt.datetime(2024, 1, 1, 9, 59)
    assert store.get_slice(end_dt, 5) == ()


def test_get_slice_end_dt_equals_first_bar(make_store):
    store = make_store(["2024-01-01 10:00", "2024-01-01 10:01"])
    end_dt = dt.datetime(2024, 1, 1, 10, 0)
    result = store.get_slice(end_dt, 5)
    assert [b.timestamp.minute for b in result] == [0]


def test_get_slice_end_dt_after_last_bar(make_store):
    store = make_store(["2024-01-01 10:00", "2024-01-01 10:01"])
    end_dt = dt.datetime(2024, 1, 1, 10, 5)
    result = store.get_slice(end_dt, 1)
    assert [b.timestamp.minute for b in result] == [1]


def test_get_slice_duplicate_timestamps_exact_match(make_bar):
    bars = [
        make_bar("2024-01-01 10:00"),
        make_bar("2024-01-01 10:00"),
        make_bar("2024-01-01 10:01"),
    ]
    store = DataStore(bars)
    end_dt = dt.datetime(2024, 1, 1, 10, 0)
    result = store.get_slice(end_dt, 10)
    assert len(result) == 2
    assert all(b.timestamp.minute == 0 for b in result)


def test_get_slice_duplicate_timestamps_mid_range(make_bar):
    bars = [
        make_bar("2024-01-01 10:00"),
        make_bar("2024-01-01 10:00"),
        make_bar("2024-01-01 10:01"),
    ]
    store = DataStore(bars)
    end_dt = dt.datetime(2024, 1, 1, 10, 0, 30)
    result = store.get_slice(end_dt, 10)
    assert len(result) == 2
    assert all(b.timestamp.minute == 0 for b in result)


def test_get_slice_day_boundary_behavior(make_store):
    store = make_store(["2024-01-01 23:59", "2024-01-02 00:00"])
    end_dt = dt.datetime(2024, 1, 1, 23, 59)
    result = store.get_slice(end_dt, 5)
    assert [b.timestamp.strftime("%H:%M") for b in result] == ["23:59"]


# ---------------------------------------------------------------------------
# n-boundary conditions
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "n,expected_len",
    [
        (0, 0),
        (-5, 0),
        (999, 2),
    ],
)
def test_get_slice_n_boundaries(make_store, n, expected_len):
    store = make_store(["2024-01-01 10:00", "2024-01-01 10:01"])
    end_dt = dt.datetime(2024, 1, 1, 10, 1)
    result = store.get_slice(end_dt, n)
    assert len(result) == expected_len


# ---------------------------------------------------------------------------
# Dataset integrity
# ---------------------------------------------------------------------------

def test_get_slice_unsorted_input_is_sorted(make_bar):
    bars = [
        make_bar("2024-01-01 10:02"),
        make_bar("2024-01-01 10:00"),
        make_bar("2024-01-01 10:01"),
    ]
    store = DataStore(bars)
    end_dt = dt.datetime(2024, 1, 1, 10, 2)
    result = store.get_slice(end_dt, 3)
    assert [b.timestamp.minute for b in result] == [0, 1, 2]


def test_get_slice_empty_datastore():
    store = DataStore([])
    end_dt = dt.datetime(2024, 1, 1, 10, 0)
    assert store.get_slice(end_dt, 5) == ()


# ---------------------------------------------------------------------------
# Invalid input handling
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("end_dt", [None, 12345])
def test_get_slice_invalid_end_dt_raises(make_store, end_dt):
    store = make_store(["2024-01-01 10:00"])
    with pytest.raises(TypeError):
        store.get_slice(end_dt, 5)


def test_get_slice_invalid_n_type_raises(make_store):
    store = make_store(["2024-01-01 10:00"])
    with pytest.raises(TypeError):
        store.get_slice(dt.datetime(2024, 1, 1, 10, 0), "abc")


def test_get_slice_invalid_timestamp_type_raises():
    class FakeBar:
        timestamp = 123  # invalid type

    store = DataStore([FakeBar()])
    with pytest.raises(TypeError):
        store.get_slice(dt.datetime(2024, 1, 1, 10, 0), 5)


# ---------------------------------------------------------------------------
# Slicing behavior
# ---------------------------------------------------------------------------

def test_get_slice_returns_tuple(make_store):
    store = make_store(["2024-01-01 10:00"])
    end_dt = dt.datetime(2024, 1, 1, 10, 0)
    result = store.get_slice(end_dt, 1)
    assert isinstance(result, tuple)


# ============================================================================
# Tests for DataStore.next_slice
# ============================================================================

# ---------------------------------------------------------------------------
# Input validation & exceptions
# ---------------------------------------------------------------------------

def test_next_slice_raises_on_steps_zero(make_store):
    store = make_store(["2024-01-01 00:00"])
    with pytest.raises(ValueError):
        store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=0, n=1)


def test_next_slice_raises_on_steps_negative(make_store):
    store = make_store(["2024-01-01 00:00"])
    with pytest.raises(ValueError):
        store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=-1, n=1)


def test_next_slice_type_error_on_non_datetime_current_dt(make_store):
    store = make_store(["2024-01-01 00:00"])
    with pytest.raises(TypeError):
        store.next_slice("not-a-datetime", steps=1, n=1)


# ---------------------------------------------------------------------------
# Empty and minimal datasets
# ---------------------------------------------------------------------------

def test_next_slice_empty_dataset_returns_empty():
    store = DataStore([])
    result = store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=1, n=1)
    assert result == ()


def test_next_slice_single_bar_valid(make_store):
    store = make_store(["2024-01-01 00:00"])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=1, n=1)
    assert len(result) == 1
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 0, 0)


def test_next_slice_single_bar_no_future_data(make_store):
    store = make_store(["2024-01-01 00:00"])
    result = store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=1, n=1)
    assert result == ()


# ---------------------------------------------------------------------------
# Dataset ordering and duplicates
# ---------------------------------------------------------------------------

def test_next_slice_unsorted_input_bars_are_sorted(make_store):
    store = make_store([
        "2024-01-01 02:00",
        "2024-01-01 00:00",
        "2024-01-01 01:00",
    ])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=2, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 1, 0)


def test_next_slice_duplicate_timestamps(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 00:00",
        "2024-01-01 01:00",
    ])
    result = store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=1, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 1, 0)


# ---------------------------------------------------------------------------
# Bisect behavior scenarios
# ---------------------------------------------------------------------------

def test_next_slice_current_dt_before_first_bar(make_store):
    store = make_store(["2024-01-01 00:00", "2024-01-01 01:00"])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=1, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 0, 0)


def test_next_slice_current_dt_exact_match(make_store):
    store = make_store(["2024-01-01 00:00", "2024-01-01 01:00"])
    result = store.next_slice(dt.datetime(2024, 1, 1, 0, 0), steps=1, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 1, 0)


def test_next_slice_current_dt_between_bars(make_store):
    store = make_store(["2024-01-01 00:00", "2024-01-01 02:00"])
    result = store.next_slice(dt.datetime(2024, 1, 1, 1, 0), steps=1, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 2, 0)


def test_next_slice_current_dt_after_last_bar(make_store):
    store = make_store(["2024-01-01 00:00"])
    result = store.next_slice(dt.datetime(2024, 1, 2, 0, 0), steps=1, n=1)
    assert result == ()


# ---------------------------------------------------------------------------
# Target index boundary cases
# ---------------------------------------------------------------------------

def test_next_slice_target_idx_exact_last_bar(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 01:00",
        "2024-01-01 02:00",
    ])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=3, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 2, 0)


def test_next_slice_target_idx_equal_len_returns_empty(make_store):
    store = make_store(["2024-01-01 00:00", "2024-01-01 01:00"])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=3, n=1)
    assert result == ()


def test_next_slice_target_idx_greater_than_len_returns_empty(make_store):
    store = make_store(["2024-01-01 00:00"])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=5, n=1)
    assert result == ()


# ---------------------------------------------------------------------------
# Interaction with get_slice
# ---------------------------------------------------------------------------

def test_next_slice_n_larger_than_remaining_bars(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 01:00",
        "2024-01-01 02:00",
    ])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=2, n=5)
    assert len(result) == 2
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 0, 0)
    assert result[1].timestamp == dt.datetime(2024, 1, 1, 1, 0)


def test_next_slice_get_slice_end_dt_between_bars(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 02:00",
        "2024-01-01 04:00",
    ])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=2, n=2)
    assert len(result) == 2
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 0, 0)
    assert result[1].timestamp == dt.datetime(2024, 1, 1, 2, 0)


# ---------------------------------------------------------------------------
# Functional behavior
# ---------------------------------------------------------------------------

def test_next_slice_sliding_window_sequence(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 01:00",
        "2024-01-01 02:00",
        "2024-01-01 03:00",
    ])

    s1 = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=1, n=1)
    assert s1[0].timestamp == dt.datetime(2024, 1, 1, 0, 0)

    s2 = store.next_slice(s1[-1].timestamp, steps=1, n=1)
    assert s2[0].timestamp == dt.datetime(2024, 1, 1, 1, 0)

    s3 = store.next_slice(s2[-1].timestamp, steps=1, n=1)
    assert s3[0].timestamp == dt.datetime(2024, 1, 1, 2, 0)


def test_next_slice_steps_greater_than_one(make_store):
    store = make_store([
        "2024-01-01 00:00",
        "2024-01-01 01:00",
        "2024-01-01 02:00",
        "2024-01-01 03:00",
    ])
    result = store.next_slice(dt.datetime(2023, 12, 31, 0, 0), steps=3, n=1)
    assert result[0].timestamp == dt.datetime(2024, 1, 1, 2, 0)
