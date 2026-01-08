# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""OHLCV bar store in memory with efficient timestamp-based access."""

from __future__ import annotations
import bisect
import datetime as dt
from pathlib import Path
import csv

from volume_companion.bar import Bar


class DataStore:
    """In-memory OHLCV bar store with fast timestamp lookup."""

    def __init__(self, bars: list[Bar]):
        """Initialise DataStore with sorted bars."""
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)

        self._bars: tuple[Bar, ...] = tuple(sorted_bars)
        self._timestamps: list[dt.datetime] = [b.timestamp for b in self._bars]

    @classmethod
    def load_csv(cls, path: str | Path) -> DataStore:
        """
        Load OHLCV bars from a CSV file of fixed format.

        Malformed rows are skipped with a concise warning.
        """
        bars: list[Bar] = []

        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"CSV file not found: {path}")

        if path.suffix.lower() != ".csv":
            print(f"Loading file without CSV extension: {path.name}")

        timestamp_format = "%Y.%m.%d %H:%M"

        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)

            skipped = 0

            for line_no, row in enumerate(reader, start=1):
                if len(row) != 7:
                    skipped += 1
                    print(f"Skipping CSV row {line_no}: expected 7 columns")
                    continue

                try:
                    timestamp = dt.datetime.strptime(
                        f"{row[0]} {row[1]}",
                        timestamp_format,
                    )

                    bars.append(
                        Bar(
                            timestamp=timestamp,
                            open_=float(row[2]),
                            high=float(row[3]),
                            low=float(row[4]),
                            close=float(row[5]),
                            volume=float(row[6]),
                        )
                    )
                except (ValueError, TypeError) as exc:
                    skipped += 1
                    print(f"Skipping CSV row {line_no}: {exc}")
                    continue

        if not bars:
            raise ValueError("CSV contains no valid OHLCV rows")

        if skipped:
            print(f"Skipped {skipped} malformed CSV rows")

        return cls(bars)

    def get_slice(self, end_dt: dt.datetime, n: int) -> tuple[Bar, ...]:
        """
        Return up to n bars ending at or before end_dt.
        Returns empty tuple if end_dt is before first bar.
        """
        idx = bisect.bisect_right(self._timestamps, end_dt) - 1
        if idx < 0:
            return ()
        start = max(0, idx - n + 1)
        return self._bars[start:idx + 1]

    def next_slice(
        self,
        current_dt: dt.datetime,
        steps: int,
        n: int,
    ) -> tuple[Bar, ...]:
        """
        Return the next window of n bars after current_dt,
        advanced forward by `steps` bars.
        Returns empty tuple if no further data is available.
        """
        if steps <= 0:
            raise ValueError(f"Steps must be positive, got {steps}")

        start_idx = bisect.bisect_right(self._timestamps, current_dt)
        target_idx = start_idx + steps - 1

        if target_idx >= len(self._bars):
            return ()

        return self.get_slice(self._timestamps[target_idx], n)

    @property
    def bar_count(self) -> int:
        """Return number of bars loaded."""
        return len(self._bars)
