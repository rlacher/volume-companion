# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for Bar validation: check_high, check_low."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from volume_companion.bar import Bar


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_kwargs():
    """Base valid kwargs for constructing a Bar instance."""
    return {
        "timestamp": datetime(2025, 1, 1),
        "open_": 10.0,
        "high": 12.0,
        "low": 8.0,
        "close": 11.0,
        "volume": 100.0,
    }


@pytest.fixture
def make_bar(base_kwargs):
    """Factory fixture to create Bar instances with overrides."""
    def _factory(**overrides):
        data = base_kwargs.copy()
        data.update(overrides)
        return Bar(**data)
    return _factory


# ---------------------------------------------------------------------------
# Valid construction tests
# ---------------------------------------------------------------------------

def test_bar_construction_with_valid_data(make_bar):
    """Bar can be constructed with valid OHLCV data."""
    bar = make_bar()
    assert bar.open_ == 10.0
    assert bar.high == 12.0
    assert bar.low == 8.0
    assert bar.close == 11.0
    assert bar.volume == 100.0


def test_bar_construction_equal_values_allowed(make_bar):
    """Bar allows open, high, low, close to be equal if consistent."""
    bar = make_bar(open_=10.0, high=10.0, low=10.0, close=10.0)
    assert bar.high == 10.0
    assert bar.low == 10.0


# ---------------------------------------------------------------------------
# Invalid data tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "high": 5.0,
            "low": 6.0,
            "open_": 5.5,
        },  # high < low, high < open, low > open
        {
            "low": 15.0,
            "high": 12.0,
            "open_": 14.0,
        },  # low > high, low > open
        {
            "high": 9.0,
            "low": 5.0,
            "open_": 10.0,
        },  # high < open
        {
            "low": 8.0,
            "high": 12.0,
            "open_": 9.0,
            "close": -1.0,
        },  # negative close
    ],
)
def test_bar_invalid_data_raises_validation(make_bar, kwargs):
    """Semi-permissive test: any invalid OHLCV combination raises."""
    with pytest.raises(ValidationError):
        make_bar(**kwargs)
