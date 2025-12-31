#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Executable entry point for the Volume Companion CLI."""

import argparse
import logging
import sys
from pathlib import Path

from volume_companion.cli import VolumeCLI
from volume_companion.session_state import SessionState


def _configure_logging() -> None:
    """Configure lean console logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def parse_args() -> Path:
    """Parse and validate CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Volume Companion",
    )
    parser.add_argument(
        "csv_path",
        help="Path to OHLCV CSV file",
    )
    args = parser.parse_args()

    path = Path(args.csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    return path


def main() -> None:
    """CLI entrypoint."""
    _configure_logging()

    csv_path = parse_args()
    session_state = SessionState()

    VolumeCLI(csv_path, session_state).cmdloop()


if __name__ == "__main__":
    main()
