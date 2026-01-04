# SPDX-License-Identifier: MIT
# Copyright (c) 2025 René Lacher
"""Provides a formatter for console output of volume data."""

import sys
from typing import List

from volume_companion.bar import Bar


class Formatter:
    """Pure formatting utilities for console output."""

    _BLOCKS = "▁▂▃▄▅▆▇█"
    _ROWS = 5
    _LEVELS_PER_ROW = len(_BLOCKS)
    _MAX_LEVEL = _ROWS * _LEVELS_PER_ROW

    _GREEN = "\033[92m"
    _RED = "\033[91m"
    _RESET = "\033[0m"

    @staticmethod
    def supports_colour() -> bool:
        """Return True if ANSI colours are likely supported."""
        return sys.stdout.isatty()

    @classmethod
    def format_ascii_volume(
        cls,
        bars: List["Bar"],
        colour_enabled: bool = True
    ) -> str:
        """Return a multi-line ASCII volume histogram for the given bars."""
        if not bars:
            return "(no data)"

        max_volume = max(bar.volume for bar in bars)
        if max_volume <= 0:
            return "(no volume)"

        heights = [
            cls._scaled_height(bar.volume, max_volume)
            for bar in bars
        ]

        use_colour = colour_enabled and cls.supports_colour()
        lines: List[str] = []

        for row in range(cls._ROWS):
            threshold = cls._MAX_LEVEL - (row + 1) * cls._LEVELS_PER_ROW
            line_chars = []

            for bar, height in zip(bars, heights):
                remaining = max(0, height - threshold)

                if remaining <= 0:
                    char = " "
                elif remaining >= cls._LEVELS_PER_ROW:
                    char = cls._BLOCKS[-1]
                else:
                    char = cls._BLOCKS[remaining - 1]

                if use_colour and char != " ":
                    colour = cls._GREEN if bar.close >= bar.open_ else cls._RED
                    char = f"{colour}{char}{cls._RESET}"

                line_chars.append(char)

            lines.append(" ".join(line_chars))

        return "\n".join(lines)

    @staticmethod
    def format_verbose(bars: List["Bar"]) -> str:
        """Return verbose OHLCV output for the given bars."""
        return "\n".join(
            (
                f"{bar.timestamp:%Y-%m-%d %H:%M} | "
                f"O:{bar.open_:.4f} H:{bar.high:.4f} "
                f"L:{bar.low:.4f} C:{bar.close:.4f} | "
                f"Vol:{int(bar.volume)} | "
                f"{'↑' if bar.close >= bar.open_ else '↓'}"
            )
            for bar in bars
        )

    @classmethod
    def _scaled_height(cls, volume: float, max_volume: float) -> int:
        """Return the scaled height for a given volume."""
        if volume <= 0 or max_volume <= 0:
            return 0

        scaled = int(round(volume / max_volume * cls._MAX_LEVEL))
        return max(1, min(cls._MAX_LEVEL, scaled))
