# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""Unit tests for Bar validation: check_high, check_low, check_close."""

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


def test_bar_construction_zero_values_allowed(make_bar):
    """Bar accepts zero as the lower bound for prices and volume."""
    bar = make_bar(open_=0.0, high=0.0, low=0.0, close=0.0, volume=0.0)
    assert bar.high == 0.0
    assert bar.volume == 0.0


# ---------------------------------------------------------------------------
# Invalid data tests
# ---------------------------------------------------------------------------

def test_high_below_open_raises(make_bar):
    """high < open is rejected by the high validator."""
    with pytest.raises(ValidationError, match="high must be >= open"):
        make_bar(open_=10.0, high=9.0, low=5.0)


def test_low_above_high_raises(make_bar):
    """low > high is rejected by the low validator."""
    with pytest.raises(ValidationError, match="low must be <= high"):
        make_bar(open_=10.0, high=12.0, low=13.0)


def test_low_above_open_raises(make_bar):
    """low > open is rejected even when low <= high."""
    with pytest.raises(ValidationError, match="low must be <= open"):
        make_bar(open_=10.0, high=12.0, low=11.0)


def test_close_above_high_raises(make_bar):
    """close > high is rejected by the close validator."""
    with pytest.raises(ValidationError, match="close must be <= high"):
        make_bar(close=13.0)


def test_close_below_low_raises(make_bar):
    """close < low is rejected by the close validator."""
    with pytest.raises(ValidationError, match="close must be >= low"):
        make_bar(close=7.0)


@pytest.mark.parametrize(
    "field",
    ["open_", "high", "low", "close", "volume"],
)
def test_negative_values_raise(make_bar, field):
    """Negative prices and volume are rejected at the field boundary."""
    with pytest.raises(
        ValidationError,
        match="greater than or equal to 0",
    ):
        make_bar(**{field: -0.01})


@pytest.mark.parametrize(
    "field",
    ["open_", "high", "low", "close", "volume"],
)
def test_non_finite_values_raise(make_bar, field):
    """Infinite prices and volume are rejected."""
    with pytest.raises(ValidationError, match="finite"):
        make_bar(**{field: float("inf")})
