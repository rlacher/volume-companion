# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Prompt-based CLI interface."""

import cmd
from pathlib import Path

from pydantic_core import ValidationError
from volume_companion.session_state import SessionState


class VolumeCLI(cmd.Cmd):
    """Interactive command loop."""

    intro = "Volume Companion - type 'help' or 'quit'"
    prompt = "> "

    def __init__(self, csv_path: Path, state: SessionState) -> None:
        """Initialise CLI with injected session state."""
        super().__init__()
        self.csv_path = csv_path
        self.state = state

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
        self._query_datetime()

    def do_step(self, arg: str) -> None:
        """Advance one bar: step"""
        self._step()

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

    def _query_datetime(self) -> None:
        """Query data for current datetime (placeholder)."""
        print("Queried data (placeholder)")

    def _step(self) -> None:
        """Advance to next bar (placeholder)."""
        print("Step executed (placeholder)")
