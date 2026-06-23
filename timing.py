from __future__ import annotations

import time


def is_fresh(timestamp: float, max_age: float) -> bool:
    if timestamp <= 0.0:
        return False
    return (time.monotonic() - timestamp) <= max_age


class Rate:
    """Simple loop-rate helper using monotonic time."""

    def __init__(self, hz: float) -> None:
        if hz <= 0.0:
            raise ValueError("Rate must be positive")
        self._period = 1.0 / hz
        self._next_time = time.monotonic() + self._period

    def sleep(self) -> None:
        now = time.monotonic()
        delay = self._next_time - now
        if delay > 0.0:
            time.sleep(delay)
            self._next_time += self._period
        else:
            self._next_time = now + self._period
