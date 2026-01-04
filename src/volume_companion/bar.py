# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Defines the Bar data structure."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Bar(BaseModel):
    """Represents a single OHLCV bar with validation."""
    timestamp: datetime
    open_: float = Field(..., ge=0)
    high: float = Field(..., ge=0)
    low: float = Field(..., ge=0)
    close: float = Field(..., ge=0)
    volume: float = Field(..., ge=0)

    @field_validator("high")
    @classmethod
    def check_high(cls, v, info):
        low = info.data.get("low")
        open_ = info.data.get("open")
        if low is not None and v < low:
            raise ValueError("high must be >= low")
        if open_ is not None and v < open_:
            raise ValueError("high must be >= open")
        return v

    @field_validator("low")
    @classmethod
    def check_low(cls, v, info):
        high = info.data.get("high")
        open_ = info.data.get("open")
        if high is not None and v > high:
            raise ValueError("low must be <= high")
        if open_ is not None and v > open_:
            raise ValueError("low must be <= open")
        return v

    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        slots=True
    )
