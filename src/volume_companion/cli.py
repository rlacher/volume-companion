# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Prompt-based CLI interface."""

import cmd
import logging
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

        logging.info(f"Loaded CSV: {csv_path.name}")

    def do_bars(self, arg: str) -> None:
        """Set number of displayed bars: bars <int>"""
        try:
            self.state.bars = int(arg)
            logging.info("bars=%s", self.state.bars)
        except (ValueError, ValidationError):
            logging.info("Invalid bars value: %s", arg)

    def do_offset(self, arg: str) -> None:
        """Set timezone offset: offset <int>"""
        try:
            self.state.offset = int(arg)
            logging.info("offset=%s", self.state.offset)
        except (ValueError, ValidationError):
            logging.info("Invalid offset value: %s", arg)

    def do_verbose(self, arg: str) -> None:
        """Toggle verbose mode: verbose"""
        self.state.toggle_verbose()
        logging.info("verbose=%s", self.state.verbose)

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
        return self.do_quit(arg)

    def _show_config(self) -> None:
        """Display current session configuration."""
        logging.info(
            "bars=%s, offset=%s, verbose=%s, datetime=%s",
            self.state.bars,
            self.state.offset,
            self.state.verbose,
            self.state.datetime,
        )

    def _step(self) -> None:
        """Advance to next bar (placeholder)."""
        logging.info("Step executed (placeholder)")

    def default(self, line: str) -> None:
        """Handle unknown commands."""
        logging.info("Unknown command: %s", line)

    def emptyline(self) -> bool:
        """Ignore empty input."""
        return False
