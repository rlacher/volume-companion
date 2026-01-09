# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for SessionState.to_raw_datetime."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from volume_companion.session_state import SessionState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_datetime():
    """Baseline datetime aligned with 1-minute granularity."""
    return datetime(2025, 1, 15, 10, 0)


@pytest.fixture
def state_factory():
    """Factory for creating SessionState instances."""

    def _factory(selected_datetime=None, offset=0):
        return SessionState(
            selected_datetime=selected_datetime,
            offset=offset,
        )

    return _factory


# ---------------------------------------------------------------------------
# Core behaviour
# ---------------------------------------------------------------------------

def test_to_raw_datetime_returns_none_when_no_selected_datetime(
    state_factory,
):
    state = state_factory()
    assert state.to_raw_datetime() is None


def test_to_raw_datetime_identity_with_zero_offset(
    state_factory,
    base_datetime,
):
    state = state_factory(selected_datetime=base_datetime, offset=0)
    assert state.to_raw_datetime() == base_datetime


def test_to_local_datetime_returns_none_when_raw_is_none(
    state_factory,
):
    state = state_factory(offset=3)
    assert state.to_local_datetime(None) is None


def test_to_local_datetime_identity_with_zero_offset(
    state_factory,
    base_datetime,
):
    state = state_factory(offset=0)
    assert state.to_local_datetime(base_datetime) == base_datetime


# ---------------------------------------------------------------------------
# Offset application
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "offset, expected",
    [
        (3, datetime(2025, 1, 15, 13, 0)),
        (-5, datetime(2025, 1, 15, 5, 0)),
    ],
)
def test_to_raw_datetime_applies_offset(
    state_factory,
    base_datetime,
    offset,
    expected,
):
    state = state_factory(
        selected_datetime=base_datetime,
        offset=offset,
    )
    assert state.to_raw_datetime() == expected


@pytest.mark.parametrize(
    "offset, expected",
    [
        (-12, datetime(2025, 1, 14, 22, 0)),
        (14, datetime(2025, 1, 16, 0, 0)),
    ],
)
def test_to_raw_datetime_offset_boundaries(
    state_factory,
    base_datetime,
    offset,
    expected,
):
    state = state_factory(
        selected_datetime=base_datetime,
        offset=offset,
    )
    assert state.to_raw_datetime() == expected


@pytest.mark.parametrize(
    "offset, expected",
    [
        (3, datetime(2025, 1, 15, 7, 0)),
        (-5, datetime(2025, 1, 15, 15, 0)),
    ],
)
def test_to_local_datetime_applies_offset(
    state_factory,
    base_datetime,
    offset,
    expected,
):
    state = state_factory(offset=offset)
    assert state.to_local_datetime(base_datetime) == expected


@pytest.mark.parametrize(
    "offset, expected",
    [
        (14, datetime(2025, 1, 14, 20, 0)),
        (-12, datetime(2025, 1, 15, 22, 0)),
    ],
)
def test_to_local_datetime_offset_boundaries(
    state_factory,
    base_datetime,
    offset,
    expected,
):
    state = state_factory(offset=offset)
    assert state.to_local_datetime(base_datetime) == expected


# ---------------------------------------------------------------------------
# Date rollover scenarios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "selected_datetime, offset, expected",
    [
        (
            datetime(2025, 1, 31, 23, 0),
            2,
            datetime(2025, 2, 1, 1, 0),
        ),
        (
            datetime(2025, 3, 1, 1, 0),
            -3,
            datetime(2025, 2, 28, 22, 0),
        ),
        (
            datetime(2024, 12, 31, 23, 0),
            2,
            datetime(2025, 1, 1, 1, 0),
        ),
    ],
)
def test_to_raw_datetime_date_rollover(
    state_factory,
    selected_datetime,
    offset,
    expected,
):
    state = state_factory(
        selected_datetime=selected_datetime,
        offset=offset,
    )
    assert state.to_raw_datetime() == expected


@pytest.mark.parametrize(
    "raw_dt, offset, expected",
    [
        (
            datetime(2025, 1, 16, 1, 0),
            2,
            datetime(2025, 1, 15, 23, 0),
        ),
        (
            datetime(2025, 1, 14, 22, 0),
            -3,
            datetime(2025, 1, 15, 1, 0),
        ),
        (
            datetime(2025, 1, 15, 1, 0),
            2,
            datetime(2025, 1, 14, 23, 0),
        ),
    ],
)
def test_to_local_datetime_date_rollover(
    state_factory,
    raw_dt,
    offset,
    expected,
):
    state = state_factory(offset=offset)
    assert state.to_local_datetime(raw_dt) == expected


# ---------------------------------------------------------------------------
# Datetime semantics
# ---------------------------------------------------------------------------

def test_to_raw_datetime_timezone_aware_datetime(
    state_factory,
):
    dt = datetime(2025, 1, 15, 10, 0, tzinfo=timezone.utc)
    state = state_factory(selected_datetime=dt, offset=2)

    assert state.to_raw_datetime() == datetime(
        2025,
        1,
        15,
        12,
        0,
        tzinfo=timezone.utc,
    )


def test_to_local_datetime_timezone_aware_datetime_preserved(
    state_factory,
):
    raw_dt = datetime(
        2025,
        1,
        15,
        10,
        0,
        tzinfo=timezone.utc,
    )
    state = state_factory(offset=2)

    assert state.to_local_datetime(raw_dt) == datetime(
        2025,
        1,
        15,
        8,
        0,
        tzinfo=timezone.utc,
    )


# ---------------------------------------------------------------------------
# Validation and assignment behaviour
# ---------------------------------------------------------------------------

def test_to_raw_datetime_parses_iso_string_on_init():
    state = SessionState(
        selected_datetime="2025-01-15T10:00",
        offset=1,
    )
    assert state.to_raw_datetime() == datetime(2025, 1, 15, 11, 0)


@pytest.mark.parametrize(
    "invalid_value",
    [
        "15-01-2025 10:00",
        "invalid-datetime",
    ],
)
def test_to_raw_datetime_rejects_invalid_string_on_init(
    invalid_value,
):
    with pytest.raises(ValueError):
        SessionState(selected_datetime=invalid_value)


def test_to_raw_datetime_assignment_validates_datetime():
    state = SessionState()

    with pytest.raises(ValueError):
        state.selected_datetime = "invalid-datetime"


def test_to_raw_datetime_assignment_validates_offset():
    state = SessionState()

    with pytest.raises(ValidationError):
        state.offset = 99


def test_to_local_datetime_offset_assignment_validation():
    state = SessionState()

    with pytest.raises(ValidationError):
        state.offset = 99


# ---------------------------------------------------------------------------
# Invariants and consistency
# ---------------------------------------------------------------------------

def test_to_raw_datetime_round_trip_identity(
    state_factory,
):
    dt = datetime(2025, 4, 10, 8, 45)
    state = state_factory(selected_datetime=dt, offset=5)

    raw = state.to_raw_datetime()
    local = state.to_local_datetime(raw)

    assert local == dt


def test_to_raw_datetime_idempotent_calls(
    state_factory,
    base_datetime,
):
    state = state_factory(
        selected_datetime=base_datetime,
        offset=-4,
    )

    first = state.to_raw_datetime()
    second = state.to_raw_datetime()

    assert first == second


def test_to_local_datetime_round_trip_with_to_raw_datetime():
    local_dt = datetime(2025, 4, 10, 8, 45)
    state = SessionState(
        selected_datetime=local_dt,
        offset=5,
    )

    raw_dt = state.to_raw_datetime()
    assert state.to_local_datetime(raw_dt) == local_dt


def test_to_local_datetime_idempotent_calls(
    state_factory,
    base_datetime,
):
    state = state_factory(offset=-4)

    first = state.to_local_datetime(base_datetime)
    second = state.to_local_datetime(base_datetime)

    assert first == second
