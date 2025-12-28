# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Prompt-based CLI interface."""

import cmd
import logging
from pathlib import Path


class SessionState:
    """Holds current interactive session configuration."""

    def __init__(self) -> None:
        self.bars: int = 10
        self.timeframe: str = "M5"
        self.offset: int = 0
        self.verbose: bool = False
        self.datetime: str | None = None


class VolumeCLI(cmd.Cmd):
    """Interactive command loop."""

    intro = "Volume Companion — type 'help' or 'quit'"
    prompt = "> "

    def __init__(self, csv_path: Path) -> None:
        """Initialise CLI and session state."""
        super().__init__()
        self.csv_path = csv_path
        self.state = SessionState()

        logging.info(f"Loaded CSV: {csv_path.name}")

    def do_bars(self, arg: str) -> None:
        """bars <int>"""
        self._set_bars(arg)

    def do_timeframe(self, arg: str) -> None:
        """timeframe <str>"""
        self._set_timeframe(arg)

    def do_offset(self, arg: str) -> None:
        """offset <int>"""
        self._set_offset(arg)

    def do_verbose(self, arg: str) -> None:
        """Toggle verbose mode."""
        self._toggle_verbose()

    def do_config(self, arg: str) -> None:
        """Show current configuration."""
        self._show_config()

    def do_step(self, arg: str) -> None:
        """Advance one bar."""
        self._step()

    def do_quit(self, arg: str) -> bool:
        """Exit the tool."""
        logging.info("Bye.")
        return True

    def do_EOF(self, arg: str) -> bool:
        """Exit on Ctrl-D."""
        logging.info("")
        return self.do_quit(arg)

    def _set_bars(self, arg: str) -> None:
        """Set number of displayed bars."""
        try:
            self.state.bars = int(arg)
            logging.info(f"Bars set to {self.state.bars}")
        except ValueError:
            logging.info("Invalid bars value")

    def _set_timeframe(self, arg: str) -> None:
        """Set timeframe."""
        if not arg:
            logging.info("Missing timeframe value")
            return
        self.state.timeframe = arg
        logging.info(f"Timeframe set to {self.state.timeframe}")

    def _set_offset(self, arg: str) -> None:
        """Set timezone offset."""
        try:
            self.state.offset = int(arg)
            logging.info(f"Offset set to {self.state.offset}")
        except ValueError:
            logging.info("Invalid offset value")

    def _toggle_verbose(self) -> None:
        """Toggle verbose mode."""
        self.state.verbose = not self.state.verbose
        logging.info(f"Verbose: {self.state.verbose}")

    def _show_config(self) -> None:
        """Display current session configuration."""
        logging.info(
            "bars=%s, timeframe=%s, offset=%s, verbose=%s, datetime=%s",
            self.state.bars,
            self.state.timeframe,
            self.state.offset,
            self.state.verbose,
            self.state.datetime,
        )

    def _step(self) -> None:
        """Advance to next bar (placeholder)."""
        logging.info("Step executed (placeholder)")

    def default(self, line: str) -> None:
        """Handle unknown commands."""
        logging.info("Unknown command")

    def emptyline(self) -> None:
        """Ignore empty input."""
        pass


def run_cli(csv_path: Path) -> None:
    """Start the interactive CLI."""
    VolumeCLI(csv_path).cmdloop()
