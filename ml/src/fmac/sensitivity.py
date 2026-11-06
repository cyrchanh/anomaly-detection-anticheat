"""Session-level mouse-sensitivity step estimator (features.yaml#sensitivity_estimator)."""
from __future__ import annotations

import math
from collections import Counter, deque

from fmac.records import TickRecord
from fmac.spec import load_spec


def step_for_slider(s: float) -> float:
    """Vanilla degrees-per-mouse-count for sensitivity slider value s in [0, 1]."""
    f = s * 0.6 + 0.2
    return f * f * f * 8.0 * 0.15


def rounding_key(x: float) -> int:
    return math.floor(x * 100000 + 0.5)


def gcd_tol(a: float, b: float, min_divisor: float) -> float:
    if a == 0:
        return 0.0
    if a < b:
        a, b = b, a
    while b > min_divisor:
        r = a - math.floor(a / b) * b
        a, b = b, r
    return a


class SensitivityEstimator:
    def __init__(self) -> None:
        cfg = load_spec()["sensitivity_estimator"]
        self._lo = cfg["accept_min_exclusive"]
        self._hi = cfg["accept_max_inclusive"]
        self._min_div = cfg["min_divisor"]
        self._min_count = cfg["min_mode_count"]
        self._range = cfg["valid_step_range"]
        self._keys: deque[int] = deque(maxlen=cfg["buffer_size"])
        self._prev_accepted: float | None = None

    def update(self, prev: TickRecord | None, cur: TickRecord) -> None:
        if (prev is None or prev.tick != cur.tick - 1 or cur.forced_rotation
                or not math.isfinite(cur.yaw) or not math.isfinite(prev.yaw)):
            self._prev_accepted = None
            return
        if not cur.rot_sent:
            return
        a = abs(cur.yaw - prev.yaw)
        if not (self._lo < a <= self._hi):
            return
        if self._prev_accepted is not None:
            g = gcd_tol(a, self._prev_accepted, self._min_div)
            if g > self._min_div:
                self._keys.append(rounding_key(g))
        self._prev_accepted = a

    def estimate(self) -> float | None:
        if not self._keys:
            return None
        counts = Counter(self._keys)
        key, n = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if n < self._min_count:
            return None
        step = key / 100000
        if not (self._range[0] <= step <= self._range[1]):
            return None
        return step
