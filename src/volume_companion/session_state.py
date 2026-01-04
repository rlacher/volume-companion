# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Holds session state for the interactive CLI."""

from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionState(BaseModel):
    """Holds current interactive session configuration."""
    bars: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=-12, le=14)
    verbose: bool = False
    selected_datetime: datetime | None = None

    @field_validator("selected_datetime", mode="before")
    @classmethod
    def parse_iso_datetime(
        cls,
        datetime_value: str | datetime | None
    ) -> datetime | None:
        """Accepts string input in ISO format and converts to datetime."""
        if datetime_value is None or isinstance(datetime_value, datetime):
            return datetime_value
        try:
            return datetime.fromisoformat(datetime_value)
        except ValueError:
            raise ValueError(
                "Invalid datetime format, expected YYYY-MM-DDTHH:MM"
            )

    def to_raw_datetime(self) -> datetime | None:
        """Convert user-selected datetime to raw CSV datetime for lookup."""
        if self.selected_datetime is None:
            return None
        return self.selected_datetime + timedelta(hours=self.offset)

    def to_local_datetime(self, raw_dt: datetime | None) -> datetime | None:
        """Convert raw CSV datetime back to user-local datetime."""
        if raw_dt is None:
            return None
        return raw_dt - timedelta(hours=self.offset)

    model_config = ConfigDict(
        validate_assignment=True
    )
