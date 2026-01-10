# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Holds session state for the interactive CLI."""

from datetime import datetime, timedelta
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SessionState(BaseModel):
    """Holds current interactive session configuration.

    Any timezone info on selected_datetime is preserved but ignored in
    offset calculations.
    """
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

    @property
    def as_server_datetime(self) -> datetime | None:
        """Convert user-selected datetime to server datetime for CSV lookup."""
        if self.selected_datetime is None:
            return None
        return self.selected_datetime + timedelta(hours=self.offset)

    def set_from_server_datetime(
        self,
        raw_dt: datetime | None
    ) -> None:
        """Set selected_datetime from server datetime with offset applied."""
        if raw_dt is None:
            self.selected_datetime = None
            return
        self.selected_datetime = raw_dt - timedelta(hours=self.offset)

    model_config = ConfigDict(
        validate_assignment=True
    )
