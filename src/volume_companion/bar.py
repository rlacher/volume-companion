# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Defines the Bar data structure."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Bar(BaseModel):
    """Represents a single OHLCV bar with validation."""
    timestamp: datetime
    open_: float = Field(..., ge=0, allow_inf_nan=False)
    high: float = Field(..., ge=0, allow_inf_nan=False)
    low: float = Field(..., ge=0, allow_inf_nan=False)
    close: float = Field(..., ge=0, allow_inf_nan=False)
    volume: float = Field(..., ge=0, allow_inf_nan=False)

    @field_validator("high")
    @classmethod
    def check_high(cls, v, info):
        open_ = info.data.get("open_")
        if open_ is not None and v < open_:
            raise ValueError("high must be >= open")
        return v

    @field_validator("low")
    @classmethod
    def check_low(cls, v, info):
        high = info.data.get("high")
        open_ = info.data.get("open_")
        if high is not None and v > high:
            raise ValueError("low must be <= high")
        if open_ is not None and v > open_:
            raise ValueError("low must be <= open")
        return v

    @field_validator("close")
    @classmethod
    def check_close(cls, v, info):
        low = info.data.get("low")
        high = info.data.get("high")
        if low is not None and v < low:
            raise ValueError("close must be >= low")
        if high is not None and v > high:
            raise ValueError("close must be <= high")
        return v

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        slots=True  # type: ignore[typeddict-unknown-key]
    )
