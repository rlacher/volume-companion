# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Prompt-based CLI interface."""

import cmd

from pydantic_core import ValidationError
from volume_companion.bar import Bar
from volume_companion.session_state import SessionState
from volume_companion.formatter import Formatter
from volume_companion.data_store import DataStore


class VolumeCLI(cmd.Cmd):
    """Interactive command loop."""

    intro = "Volume Companion - type 'help' or 'quit'"
    prompt = "> "

    def __init__(
            self,
            state: SessionState,
            formatter: Formatter,
            data_store: DataStore) -> None:
        """Initialise CLI with injected dependencies."""
        super().__init__()
        self.state = state
        self.formatter = formatter
        self.data_store = data_store

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
        if arg.strip():
            try:
                self.state.selected_datetime = arg
            except ValueError:
                print(f"Invalid datetime format: {arg}")
                return

        print(f"selected_datetime={self.state.selected_datetime}")
        bars = self._query_datetime()
        if bars:
            self._render(bars)

    def do_step(self, arg: str) -> None:
        """Advance one bar: step"""
        bars = self._step()
        if bars:
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

    def _query_datetime(self) -> tuple[Bar, ...]:
        """Query data for current datetime"""
        user_dt = self.state.selected_datetime
        if not user_dt:
            print("No valid datetime selected")
            return ()

        raw_dt = self.state.to_raw_datetime()
        bars = self.data_store.get_slice(raw_dt, self.state.bars)

        if not bars:
            print(
                "No data: Selected datetime is before the first available bar"
            )
            return bars

        last_bar = bars[-1]
        self.state.selected_datetime = self.state.to_local_datetime(
            last_bar.timestamp
        )

        if last_bar.timestamp != raw_dt:
            print(
                f"Note: No bar exactly at {user_dt}. "
                f"Showing last {len(bars)} bars ending at "
                f"{self.state.selected_datetime}."
            )

        if len(bars) < self.state.bars:
            print(
                f"Note: Only {len(bars)} bars available "
                f"(requested {self.state.bars})."
            )

        return bars

    def _step(self) -> tuple[Bar, ...]:
        """Advance to the next bar."""
        user_dt = self.state.selected_datetime
        if not user_dt:
            print("No valid datetime selected")
            return ()

        bars = self.data_store.next_slice(
            self.state.to_raw_datetime(),
            self.state.bars,
        )

        if bars:
            self.state.selected_datetime = self.state.to_local_datetime(
                bars[-1].timestamp
            )
        else:
            print("Already at last bar")

        return bars

    def _render(self, bars) -> None:
        """Render current bars using formatter."""
        print(self.formatter.format_ascii_volume(bars))
        if self.state.verbose:
            print(self.formatter.format_verbose(bars))
