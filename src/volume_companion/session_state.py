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

    def adjusted_datetime(self) -> datetime | None:
        """Selected datetime adjusted by timezone offset for internal raw
        data lookup."""
        if self.selected_datetime is None:
            return None
        return self.selected_datetime + timedelta(hours=self.offset)

    model_config = ConfigDict(
        validate_assignment=True
    )
