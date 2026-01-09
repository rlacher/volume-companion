# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for SessionState."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from volume_companion.session_state import SessionState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def naive_datetime() -> datetime:
    """Naive datetime instance."""
    return datetime(2025, 1, 15, 10, 0)


@pytest.fixture
def aware_datetime() -> datetime:
    """Timezone-aware datetime instance."""
    return datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# 1. Construction & ISO parsing (parse_iso_datetime)
# ---------------------------------------------------------------------------

def test_selected_datetime_none_is_accepted():
    state = SessionState(selected_datetime=None)
    assert state.selected_datetime is None


def test_naive_datetime_is_passed_through_unchanged(naive_datetime):
    state = SessionState(selected_datetime=naive_datetime)
    assert state.selected_datetime is naive_datetime


def test_timezone_aware_datetime_is_passed_through_unchanged(aware_datetime):
    state = SessionState(selected_datetime=aware_datetime)
    assert state.selected_datetime is aware_datetime
    assert state.selected_datetime.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2025-01-15", datetime(2025, 1, 15)),
        ("2025-01-15T10:00", datetime(2025, 1, 15, 10, 0)),
        ("2025-01-15 10:00", datetime(2025, 1, 15, 10, 0)),
    ],
)
def test_valid_iso_strings_are_parsed(value, expected):
    state = SessionState(selected_datetime=value)
    assert state.selected_datetime == expected


def test_iso_string_with_timezone_offset_is_parsed():
    state = SessionState(selected_datetime="2025-01-15T10:00+01:00")
    parsed = state.selected_datetime

    assert parsed.tzinfo is not None
    assert parsed.utcoffset().total_seconds() == 3600


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "2025",
        "2025-01",
        "2025-01-15T",
        "2025-13-01",
        "2025-02-29",      # non-leap year
        "2025-01-15T25:00",
        "2025-001",        # unsupported ISO variant
    ],
)
def test_invalid_iso_strings_raise_value_error(value):
    with pytest.raises(ValueError, match="Invalid datetime format"):
        SessionState(selected_datetime=value)


@pytest.mark.parametrize(
    "value",
    [123, 12.5, [], {}],
)
def test_non_string_inputs_raise_type_error(value):
    with pytest.raises(TypeError):
        SessionState(selected_datetime=value)


# ---------------------------------------------------------------------------
# 2. to_raw_datetime
# ---------------------------------------------------------------------------

def test_to_raw_datetime_returns_none_if_no_selected_datetime():
    state = SessionState()
    assert state.to_raw_datetime() is None


@pytest.mark.parametrize(
    "offset, expected",
    [
        (3, datetime(2025, 1, 15, 13, 0)),
        (-5, datetime(2025, 1, 15, 5, 0)),
    ],
)
def test_to_raw_datetime_applies_offset(naive_datetime, offset, expected):
    state = SessionState(selected_datetime=naive_datetime, offset=offset)
    assert state.to_raw_datetime() == expected


def test_to_raw_datetime_date_rollover():
    state = SessionState(
        selected_datetime=datetime(2025, 1, 31, 23, 0),
        offset=2,
    )
    assert state.to_raw_datetime() == datetime(2025, 2, 1, 1, 0)


def test_to_raw_datetime_preserves_timezone(aware_datetime):
    state = SessionState(selected_datetime=aware_datetime, offset=2)
    assert state.to_raw_datetime() == datetime(
        2025, 1, 15, 12, 0, tzinfo=timezone.utc
    )


# ---------------------------------------------------------------------------
# 3. to_local_datetime
# ---------------------------------------------------------------------------

def test_to_local_datetime_returns_none_if_raw_is_none():
    state = SessionState(offset=3)
    assert state.to_local_datetime(None) is None


@pytest.mark.parametrize(
    "offset, expected",
    [
        (3, datetime(2025, 1, 15, 7, 0)),
        (-5, datetime(2025, 1, 15, 15, 0)),
    ],
)
def test_to_local_datetime_applies_offset(naive_datetime, offset, expected):
    state = SessionState(offset=offset)
    assert state.to_local_datetime(naive_datetime) == expected


def test_to_local_datetime_date_rollover():
    state = SessionState(offset=2)
    raw_dt = datetime(2025, 1, 16, 1, 0)
    assert state.to_local_datetime(raw_dt) == datetime(2025, 1, 15, 23, 0)


def test_to_local_datetime_preserves_timezone(aware_datetime):
    state = SessionState(offset=2)
    assert state.to_local_datetime(aware_datetime) == datetime(
        2025, 1, 15, 8, 0, tzinfo=timezone.utc
    )


# ---------------------------------------------------------------------------
# 4. Validation & assignment behaviour
# ---------------------------------------------------------------------------

def test_assignment_validates_selected_datetime():
    state = SessionState()
    with pytest.raises(ValueError):
        state.selected_datetime = "invalid-datetime"


def test_assignment_validates_offset_bounds():
    state = SessionState()
    with pytest.raises(ValidationError):
        state.offset = 99


# ---------------------------------------------------------------------------
# 5. Invariants
# ---------------------------------------------------------------------------

def test_round_trip_raw_and_local_datetime_identity():
    dt = datetime(2025, 4, 10, 8, 45)
    state = SessionState(selected_datetime=dt, offset=5)

    raw = state.to_raw_datetime()
    local = state.to_local_datetime(raw)

    assert local == dt
