"""The checked-in ANALYTIC fixtures must match what the builder derives now (within tolerance),
so nobody hand-edits an expected value. Regression fixtures are exempt: they are frozen on purpose."""
from __future__ import annotations

import importlib.util
import json
import math

import pytest

from fmac.spec import SCHEMA_DIR

_spec = importlib.util.spec_from_file_location("build_fixtures", SCHEMA_DIR.parent / "ml" / "tools" / "build_fixtures.py")
bf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bf)


def _eq(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return a is not None and b is not None and math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    return a == b


def test_analytic_fixtures_match_builder(tmp_path, monkeypatch):
    monkeypatch.setattr(bf, "OUT", tmp_path)
    for fn in (bf.a01_constant_sweep, bf.a03_validity, bf.a04_tick_rules, bf.a05_no_estimate, bf.a06_yaw_precision):
        fn()
    bf.a02_lock(0, "A02_lock_lag0", "")
    bf.a02_lock(3, "A02b_follow_lag3", "")
    for new in tmp_path.glob("*.json"):
        old = json.loads((SCHEMA_DIR / "fixtures" / new.name).read_text(encoding="utf-8"))
        cur = json.loads(new.read_text(encoding="utf-8"))
        assert _eq(old["expected"], cur["expected"]), new.name
        assert _eq(old["session"], cur["session"]), new.name
