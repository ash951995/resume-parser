"""
Rate limiting and cost-ceiling protection for the resume parser.

Two independent protections:
1. Call-frequency limiting - a sliding window cap on calls per minute,
   protecting against a runaway loop/bug calling the API too fast.
2. Session cost ceiling - a hard cap on total spend, using the cumulative
   tracking already built in cost_logger.py (Monday's task) - protects
   against slow-but-steady overspend, not just fast runaway loops.
"""

import time
from collections import deque

from .cost_logger import get_session_total


class RateLimitExceeded(Exception):
    """Raised when the call-frequency limit is hit."""
    pass


class CostCeilingExceeded(Exception):
    """Raised when the session cost ceiling is hit."""
    pass


class RateLimiter:
    """
    Sliding-window call-frequency limiter. Tracks call timestamps in a
    deque and rejects a new call if too many have happened in the recent
    window - a simple, understandable implementation over a more complex
    token-bucket approach, since the goal here is a basic safety net,
    not high-throughput production traffic shaping.
    """

    def __init__(self, max_calls: int, window_seconds: float):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._call_times = deque()

    def check(self) -> None:
        """Raises RateLimitExceeded if calling right now would exceed the limit."""
        now = time.monotonic()

        # Drop timestamps outside the current window
        while self._call_times and now - self._call_times[0] > self.window_seconds:
            self._call_times.popleft()

        if len(self._call_times) >= self.max_calls:
            raise RateLimitExceeded(
                f"Rate limit hit: {self.max_calls} calls per {self.window_seconds}s exceeded."
            )

        self._call_times.append(now)


class CostCeiling:
    """
    Hard cap on cumulative session spend, checked against the running
    total already tracked in cost_log.jsonl by cost_logger.py.
    """

    def __init__(self, max_session_cost_usd: float):
        self.max_session_cost_usd = max_session_cost_usd

    def check(self) -> None:
        """Raises CostCeilingExceeded if the session has already hit the cap."""
        totals = get_session_total()
        if totals["total_cost_usd"] >= self.max_session_cost_usd:
            raise CostCeilingExceeded(
                f"Session cost ceiling hit: ${totals['total_cost_usd']:.4f} spent, "
                f"limit is ${self.max_session_cost_usd:.4f}. "
                f"({totals['total_calls']} calls made this session.)"
            )


# Sensible defaults for a learning/portfolio project - adjust as needed.
_rate_limiter = RateLimiter(max_calls=2, window_seconds=5)   # 20 calls/minute
_cost_ceiling = CostCeiling(max_session_cost_usd=1.00)          # $1 hard stop


def enforce_limits() -> None:
    """Call this before making any API request. Raises if either limit is hit."""
    _rate_limiter.check()
    _cost_ceiling.check()