# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Prompt-based CLI interface."""

import cmd
from pathlib import Path
from typing import List

from pydantic_core import ValidationError
from volume_companion.bar import Bar
from volume_companion.session_state import SessionState
from volume_companion.formatter import Formatter


class VolumeCLI(cmd.Cmd):
    """Interactive command loop."""

    intro = "Volume Companion - type 'help' or 'quit'"
    prompt = "> "

    def __init__(
            self,
            csv_path: Path,
            state: SessionState,
            formatter: Formatter) -> None:
        """Initialise CLI with injected dependencies."""
        super().__init__()
        self.csv_path = csv_path
        self.state = state
        self.formatter = formatter

        print(f"Loaded CSV: {csv_path.name}")

    def do_bars(self, arg: str) -> None:
        """Set number of displayed bars: bars <int>"""
        try:
            self.state.bars = int(arg)
            print(f"bars={self.state.bars}")
        except (ValueError, ValidationError):
            print(f"Invalid bars value: {arg}")

    def do_offset(self, arg: str) -> None:
        """Set timezone offset: offset <int>"""
        try:
            self.state.offset = int(arg)
            print(f"offset={self.state.offset}")
        except (ValueError, ValidationError):
            print(f"Invalid offset value: {arg}")

    def do_verbose(self, arg: str) -> None:
        """Toggle verbose mode: verbose"""
        self.state.verbose = not self.state.verbose
        print(f"verbose={self.state.verbose}")

    def do_config(self, arg: str) -> None:
        """Show current configuration: config"""
        print(
            f"bars={self.state.bars}, "
            f"offset={self.state.offset}, "
            f"verbose={self.state.verbose}, "
            f"selected_datetime={self.state.selected_datetime}"
        )

    def do_datetime(self, arg: str) -> None:
        """Query datetime: datetime <YYYY.MM.DD,HH:MM>"""
        self.state.selected_datetime = arg
        print(f"selected_datetime={self.state.selected_datetime}")
        bars = self._query_datetime()
        self._render(bars)

    def do_step(self, arg: str) -> None:
        """Advance one bar: step"""
        bars = self._step()
        self._render(bars)

    def do_quit(self, arg: str) -> bool:
        """Exit the tool: quit"""
        print("Bye.")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Exit on Ctrl-D."""
        return self.do_quit(arg)

    def default(self, line: str) -> None:
        """Handle unknown commands."""
        print(f"Unknown command: {line}")

    def emptyline(self) -> bool:
        """Ignore empty input."""
        return False

    def _query_datetime(self) -> List[Bar] | None:
        """Query data for current datetime (placeholder)."""
        print("Queried data (placeholder)")
        return None

    def _step(self) -> List[Bar] | None:
        """Advance to next bar (placeholder)."""
        print("Step executed (placeholder)")
        return None

    def _render(self, bars) -> None:
        """Render current bars using formatter."""
        print(self.formatter.format_ascii_volume(bars))
        if self.state.verbose:
            print(self.formatter.format_verbose(bars))
