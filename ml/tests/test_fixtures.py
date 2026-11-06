"""Golden-fixture conformance. The Java extractor (Phase 4) runs the same files."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from fmac.extractor import extract_session
from fmac.records import parse_session
from fmac.spec import SCHEMA_DIR, load_spec

FIXTURES = sorted((SCHEMA_DIR / "fixtures").glob("*.json"))


def _close(actual, expected, tol, path):
    if expected is None or isinstance(expected, (bool, str)):
        assert actual == expected, f"{path}: {actual!r} != {expected!r}"
    elif isinstance(expected, (int, float)):
        assert actual is not None, f"{path}: got None, expected {expected}"
        assert math.isclose(actual, expected, rel_tol=tol["rel"], abs_tol=tol["abs"]), f"{path}: {actual!r} != {expected!r}"
    elif isinstance(expected, dict):
        for k, v in expected.items():
            assert k in actual, f"{path}.{k} missing"
            _close(actual[k], v, tol, f"{path}.{k}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), f"{path}: length {len(actual)} != {len(expected)}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            _close(a, e, tol, f"{path}[{i}]")
    else:
        raise TypeError(type(expected))


def test_fixtures_exist():
    kinds = {json.loads(p.read_text())["kind"] for p in FIXTURES}
    assert {"analytic", "regression"} <= kinds


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.stem)
def test_fixture(path: Path):
    fx = json.loads(path.read_text(encoding="utf-8"))
    assert fx["spec_version"] == load_spec()["spec_version"], "fixture built against a different spec_version"
    res = extract_session(parse_session(fx["session"]), rule_overrides=fx["rule_overrides"] or None)
    actual = {
        "windows": [w.__dict__ for w in res.windows],
        "tick_rule_hits": res.tick_rule_hits,
        "anchors_skipped_spacing": res.anchors_skipped_spacing,
        "sensitivity_step_final": res.sensitivity_step_final,
    }
    _close(actual, fx["expected"], fx["tolerance"], fx["fixture_id"])
