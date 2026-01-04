# SPDX-License-Identifier: MIT
# Copyright (c) 2026 René Lacher
"""OHLCV bar store in memory with efficient timestamp-based access."""

from __future__ import annotations
import bisect
import datetime as dt

from volume_companion.bar import Bar


class DataStore:
    """In-memory OHLCV bar store with fast timestamp lookup."""

    def __init__(self, bars: list[Bar]):
        """Initialise DataStore with sorted bars."""
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)

        self._bars: tuple[Bar, ...] = tuple(sorted_bars)
        self._timestamps: list[dt.datetime] = [b.timestamp for b in self._bars]

    @classmethod
    def load_dummy(cls, count: int = 20) -> DataStore:
        """Create deterministic dummy bars for development."""
        now = dt.datetime.now().replace(second=0, microsecond=0)
        bars = [
            Bar(
                timestamp=now - dt.timedelta(minutes=i),
                open_=1.0 + i * 0.001,
                high=1.0 + i * 0.002,
                low=0.99 + i * 0.001,
                close=1.0 + i * 0.0015,
                volume=1000 + i * 10,
            )
            for i in reversed(range(count))
        ]
        return cls(bars)

    def get_slice(self, end_dt: dt.datetime, n: int) -> tuple[Bar, ...]:
        """
        Return up to n bars ending at or before end_dt.
        Returns empty tuple if end_dt is before first bar.
        """
        idx = bisect.bisect_right(self._timestamps, end_dt) - 1
        if idx < 0:
            return tuple()
        start = max(0, idx - n + 1)
        return self._bars[start:idx + 1]

    def next_slice(
        self,
        current_dt: dt.datetime,
        n: int
    ) -> tuple[Bar, ...] | None:
        """
        Return the next window of n bars after current_dt.
        Returns None if already at last bar.
        """
        idx = bisect.bisect_right(self._timestamps, current_dt)
        if idx >= len(self._bars):
            return None
        next_end_dt = self._timestamps[idx]
        return self.get_slice(next_end_dt, n)

    @property
    def bar_count(self) -> int:
        """Return number of bars loaded."""
        return len(self._bars)
