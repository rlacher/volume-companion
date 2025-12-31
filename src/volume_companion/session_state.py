# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Holds session state for the interactive CLI."""

from pydantic import BaseModel, ConfigDict, Field


class SessionState(BaseModel):
    """Holds current interactive session configuration."""
    model_config = ConfigDict(validate_assignment=True)
    bars: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=-12, le=14)
    verbose: bool = False
    datetime: str | None = None

    def toggle_verbose(self) -> None:
        """Toggle verbose mode."""
        self.verbose = not self.verbose
