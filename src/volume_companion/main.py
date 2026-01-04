#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Executable entry point for the Volume Companion CLI."""

import argparse
from pathlib import Path

from volume_companion.cli import VolumeCLI
from volume_companion.formatter import Formatter
from volume_companion.session_state import SessionState
from volume_companion.data_store import DataStore


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
    csv_path = parse_args()

    session_state = SessionState()
    formatter = Formatter()
    data_store = DataStore.load_dummy(10)

    print(f"Loaded CSV file {csv_path.name} with {data_store.bar_count} bars")

    VolumeCLI(
        session_state,
        formatter,
        data_store
    ).cmdloop()


if __name__ == "__main__":
    main()
