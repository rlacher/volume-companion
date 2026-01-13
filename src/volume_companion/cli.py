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
        """Query volume data for selected datetime, optionally set it.

        Usage:
            datetime
                Show volume data for the current selection.
            datetime <YYYY-MM-DDTHH:MM>
                Set selection and show its volume data.
        """
        arg = arg.strip()

        if arg:
            try:
                self.state.selected_datetime = arg
            except ValueError:
                print(f"Invalid datetime format: {arg}")
                return

        bars = self._query_datetime()
        if bars:
            self._render(bars)

    def do_step(self, arg: str) -> None:
        """Advance one or multiple bars: step, step <int>"""
        arg = arg.strip()

        try:
            steps = 1 if not arg else int(arg)
        except ValueError:
            print(f"Invalid step value: {arg}")
            return

        if steps <= 0:
            print(f"Step must be positive: {steps}")
            return

        bars = self._step(steps)
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

        server_dt = self.state.as_server_datetime
        bars = self.data_store.get_slice(server_dt, self.state.bars)

        if not bars:
            print(
                "Selected datetime is before the first available bar"
            )
            return bars

        last_bar = bars[-1]
        self.state.set_from_server_datetime(last_bar.timestamp)
        print(f"selected_datetime={self.state.selected_datetime}")

        if last_bar.timestamp != server_dt:
            print(
                f"No bar exactly at {user_dt}. "
                f"Showing last {len(bars)} bars ending at "
                f"{self.state.selected_datetime}."
            )

        if len(bars) < self.state.bars:
            print(
                f"Only {len(bars)} bars available "
                f"(requested {self.state.bars})."
            )

        return bars

    def _step(self, steps: int) -> tuple[Bar, ...]:
        """Advance by `steps` bars from selected datetime."""
        user_dt = self.state.selected_datetime
        if not user_dt:
            print("No valid datetime selected")
            return ()

        bars = self.data_store.next_slice(
            self.state.as_server_datetime,
            steps,
            self.state.bars,
        )

        if bars:
            last_bar = bars[-1].timestamp
            self.state.set_from_server_datetime(last_bar.timestamp)
            print(f"selected_datetime={self.state.selected_datetime}")
        else:
            print("Step exceeds available bars")

        return bars

    def _render(self, bars) -> None:
        """Render current bars using formatter."""
        if not self.state.verbose:
            print(self.formatter.format_ascii_volume(bars))
        else:
            print(self.formatter.format_verbose(bars))
