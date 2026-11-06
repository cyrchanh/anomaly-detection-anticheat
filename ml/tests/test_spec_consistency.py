"""The spec, the code, and the docs must agree on the feature set."""
from __future__ import annotations

from fmac.extractor import extract_session
from fmac.records import parse_session
from fmac.spec import SCHEMA_DIR, context_names, feature_names, load_spec


def _sweep_session():
    ticks = [{
        "tick": t, "yaw": 0.125 * t, "pitch": 0.0, "rot_sent": t > 0, "forced_rotation": False,
        "attack_target": 7 if t == 39 else None, "held_item": "sword", "self_pos": [0, 64, 0], "ping_ms": 50,
        "entities": {"7": {"rel": [0, 0, 3.0], "half_width": 0.3, "is_player": True}},
    } for t in range(40)]
    return parse_session({"spec_version": load_spec()["spec_version"], "ticks": ticks})


def test_extractor_emits_exactly_the_spec_features_in_order():
    w = extract_session(_sweep_session()).windows[0]
    assert list(w.features) == feature_names()
    assert list(w.context) == context_names()


def test_quant_residual_is_auxiliary_only():
    inputs = {f["name"]: f["model_input"] for f in load_spec()["features"]}
    assert inputs.pop("quant_residual_yaw") is False
    assert all(inputs.values())


def test_every_feature_declares_origin_and_transform():
    spec = load_spec()
    for f in spec["features"]:
        assert f["origin"]["status"] in {"kept", "redefined", "new"}
        assert f["model_transform"] in spec["model_transforms"]
        if f["origin"]["status"] != "new":
            assert f["origin"].get("from"), f["name"]


def test_feature_docs_list_every_feature():
    adr = (SCHEMA_DIR.parent / "docs" / "adr" / "0001-feature-redesign.md").read_text(encoding="utf-8")
    for name in feature_names() + context_names():
        assert f"`{name}`" in adr, f"{name} missing from ADR 0001"


def test_unvalidated_window_rule_is_disabled_by_default():
    rules = {r["id"]: r for r in load_spec()["rules"]}
    assert rules["HR_CENTER_LOCK"]["enabled"] is False
