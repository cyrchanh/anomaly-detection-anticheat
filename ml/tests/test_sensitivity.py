from __future__ import annotations

import math

import pytest

from fmac.records import TickRecord, to_f32
from fmac.sensitivity import SensitivityEstimator, gcd_tol, step_for_slider


def _rec(t, yaw, rot_sent=True, forced=False):
    return TickRecord(t, to_f32(yaw), 0.0, rot_sent, forced, None, "sword", (0, 0, 0), 50.0, {})


def _run(yaws, **kw):
    est = SensitivityEstimator()
    prev = None
    for t, y in enumerate(yaws):
        cur = _rec(t, y, **kw)
        est.update(prev, cur)
        prev = cur
    return est.estimate()


def test_step_formula_endpoints():
    assert step_for_slider(0.0) == pytest.approx(0.0096)
    assert step_for_slider(0.5) == pytest.approx(0.15)
    assert step_for_slider(1.0) == pytest.approx(0.6144)


def test_gcd_tol_exact_multiples():
    assert gcd_tol(0.75, 0.5, 0.0048) == pytest.approx(0.25)


@pytest.mark.parametrize("slider", [0.1, 0.35, 0.5, 0.8])
def test_recovers_step_from_float32_accumulated_counts(slider):
    """Simulates the client: yaw is binary32 and each tick adds counts*step (float error included)."""
    step = step_for_slider(slider)
    counts = [3, 5, 2, 7, 4, 6, 3, 9, 2, 5, 8, 3, 4, 7, 5, 2, 6, 3, 5, 4] * 3
    yaw = 12.0
    yaws = [yaw]
    for c in counts:
        yaw = to_f32(yaw + to_f32(c * step))
        yaws.append(yaw)
    est = _run(yaws)
    assert est is not None
    assert est == pytest.approx(step, abs=2e-5)


def test_unquantised_rotation_gives_no_estimate():
    import random
    rng = random.Random(0)
    yaws = [0.0]
    for _ in range(80):
        yaws.append(yaws[-1] + rng.uniform(0.3, 4.0))
    assert _run(yaws) is None


def test_forced_rotation_resets_pairing():
    est = SensitivityEstimator()
    a = _rec(0, 0.0)
    b = _rec(1, 0.5)
    c = _rec(2, 90.0, forced=True)
    est.update(None, a)
    est.update(a, b)
    est.update(b, c)
    assert est._prev_accepted is None
    assert math.isfinite(b.yaw)
