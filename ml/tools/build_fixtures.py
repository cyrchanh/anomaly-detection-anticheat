"""Builds schema/fixtures/*.json — the golden fixtures both extractors must pass.

Two kinds, and they are labelled differently on purpose:

* kind="analytic": expected values are derived HERE from closed-form maths
  (numpy over the known generating parameters), NOT by calling the extractor.
  They test that the Python reference actually implements the spec.
* kind="regression": expected values are FROZEN OUTPUT of the Python reference.
  They cannot catch a Python bug; they exist so the Java port is checked on
  realistic, trig-heavy numerics. Regenerate only with a spec_version bump.

Usage:  python ml/tools/build_fixtures.py            (writes schema/fixtures/)
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "ml" / "src"))

from fmac.extractor import extract_session  # noqa: E402  (regression fixtures only)
from fmac.records import encode_float, parse_session  # noqa: E402
from fmac.spec import load_spec  # noqa: E402

OUT = REPO / "schema" / "fixtures"
SPEC_VERSION = load_spec()["spec_version"]
W = load_spec()["window"]["length_deltas"]
R_PLAYER_AT_3 = math.degrees(math.atan2(0.3, 3.0))  # angular radius of a 0.3-half-width hitbox at 3 blocks


def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def tick(t, yaw, pitch=0.0, *, rot_sent=True, forced=False, attack=None, held="sword",
         pos=(0.0, 64.0, 0.0), ping=50.0, entities=None):
    return {
        "tick": t, "yaw": encode_float(yaw), "pitch": encode_float(pitch), "rot_sent": rot_sent,
        "forced_rotation": forced, "attack_target": attack, "held_item": held,
        "self_pos": list(pos), "ping_ms": ping,
        "entities": {str(k): v for k, v in (entities or {}).items()},
    }


def ent(rel, half_width=0.3, is_player=True):
    return {"rel": list(rel), "half_width": half_width, "is_player": is_player}


AHEAD3 = {7: ent((0.0, 0.0, 3.0))}


def write(fixture: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{fixture['fixture_id']}.json"
    # sanity: every fixture session must satisfy the JSON schema
    parse_session(fixture["session"])
    path.write_text(json.dumps(fixture, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    print("wrote", path.name)


def base(fixture_id, kind, description, ticks, expected, overrides=None, tolerance=None):
    return {
        "fixture_id": fixture_id, "kind": kind, "spec_version": SPEC_VERSION,
        "description": description,
        "provenance": "synthetic-fixture (hand-constructed; not training data)",
        "rule_overrides": overrides or {},
        "tolerance": tolerance or load_spec()["numerics"]["default_fixture_tolerance"],
        "session": {"spec_version": SPEC_VERSION, "ticks": ticks},
        "expected": expected,
    }


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() < 1e-9 or y.std() < 1e-9:
        return 0.0
    return float(((x - x.mean()) * (y - y.mean())).mean() / (x.std() * y.std()))


# --------------------------------------------------------------------------- A01
def a01_constant_sweep():
    step = 0.125  # exactly representable; corresponds to slider s ~= 0.4509
    ticks = [tick(t, step * t, rot_sent=t > 0, attack=7 if t == 39 else None, entities=AHEAD3) for t in range(40)]
    ts = np.arange(19, 40)
    e = step * ts / R_PLAYER_AT_3   # target dead ahead, pitch 0 => error == yaw angle
    exp_w = {
        "anchor_tick": 39, "target_id": 7, "valid": True, "quant_unavailable_reason": None,
        "features": {
            "speed_mean": step, "speed_max": step, "accel_mean": 0.0, "jitter_ratio": 0.0,
            "path_straightness": 1.0, "pitch_share": 0.0,
            "aim_err_attack": float(e[-1]), "aim_err_track_mean": float(e.mean()), "aim_err_track_std": float(e.std()),
            "track_corr_lag0": 0.0, "track_corr_lag3": 0.0, "quant_residual_yaw": 0.0,
        },
        "context": {"weapon_class": "sword", "target_distance": 3.0, "target_ang_speed": 0.0, "self_speed": 0.0, "ping_ms": 50.0},
        "rule_hits": [],
    }
    write(base("A01_constant_sweep", "analytic",
               "Constant +0.125 deg/tick yaw sweep past a stationary player 3 blocks dead ahead. "
               "Aim error equals yaw angle; target bearing is constant so both correlations are defined as 0.",
               ticks, {"windows": [exp_w], "tick_rule_hits": [], "anchors_skipped_spacing": 0, "sensitivity_step_final": step}))


# --------------------------------------------------------------------------- A02
LOCK_DELTAS = [1.5, 1.25, 2.0, 1.125, 1.75, 1.5, 2.25, 1.375, 1.0 + 0.125, 1.625,
               2.0, 1.25, 1.875, 1.5, 1.125, 2.125, 1.75, 1.25, 1.5, 2.0]


def _orbit_session(lag: int):
    """Warm-up 0.125 sweep (so the step estimate is 0.125), then the target orbits at 3 blocks
    with LOCK_DELTAS bearing increments and the player's yaw follows the bearing `lag` ticks late."""
    warm = 30
    phi = [0.125 * t for t in range(warm)]
    for d in LOCK_DELTAS:
        phi.append(phi[-1] + d)
    n = len(phi)
    ticks = []
    for t in range(n):
        p = math.radians(phi[t])
        rel = (-3.0 * math.sin(p), 0.0, 3.0 * math.cos(p))
        yaw = phi[max(t - lag, 0)] if t >= warm else phi[t]
        ticks.append(tick(t, yaw, rot_sent=t > 0, attack=7 if t == n - 1 else None, entities={7: ent(rel)}))
    return ticks, phi, warm


def a02_lock(lag: int, fid: str, desc: str):
    ticks, phi, warm = _orbit_session(lag)
    n = len(phi)
    win_t = np.arange(n - W - 1, n)            # record ticks in the window
    bear = np.array(phi)                        # bearing of target per tick (exact by construction)
    yaw = np.array([phi[max(t - lag, 0)] if t >= warm else phi[t] for t in range(n)])
    dy = np.diff(yaw[win_t])
    x = np.diff(bear[win_t])
    s = np.abs(dy)
    jit_num = sum(abs(dy[i] - (dy[i - 1] + dy[i] + dy[i + 1]) / 3) for i in range(1, W - 1))
    jit_den = sum(s[1:W - 1])
    e = np.radians(np.abs(yaw[win_t] - bear[win_t]))  # error in degrees below, pitch 0
    e = np.degrees(e) / R_PLAYER_AT_3
    feats = {
        "speed_mean": float(s.mean()), "speed_max": float(s.max()),
        "accel_mean": float(np.abs(np.diff(dy)).mean()),
        "jitter_ratio": float(jit_num / jit_den) if jit_den >= 1e-9 else 0.0,
        "path_straightness": float(abs(dy.sum()) / s.sum()), "pitch_share": 0.0,
        "aim_err_attack": float(e[-1]), "aim_err_track_mean": float(e.mean()), "aim_err_track_std": float(e.std()),
        "track_corr_lag0": pearson(x, dy), "track_corr_lag3": pearson(x[:-3], dy[3:]),
        "quant_residual_yaw": 0.0,
    }
    tgt_speed = np.abs(x)
    run = best = 0
    for i in range(W):
        if e[i + 1] < 0.02 and tgt_speed[i] > 1.0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    exp_w = {
        "anchor_tick": n - 1, "target_id": 7, "valid": True, "quant_unavailable_reason": None, "features": feats,
        "context": {"weapon_class": "sword", "target_distance": 3.0, "target_ang_speed": float(tgt_speed.mean()),
                    "self_speed": 0.0, "ping_ms": 50.0},
        "rule_hits": ["HR_CENTER_LOCK"] if best >= 8 else [],
    }
    write(base(fid, "analytic", desc, ticks,
               {"windows": [exp_w], "tick_rule_hits": [], "anchors_skipped_spacing": 0, "sensitivity_step_final": 0.125},
               overrides={"HR_CENTER_LOCK": True},
               tolerance={"rel": 1e-9, "abs": 1e-7}))


# --------------------------------------------------------------------------- A03
def a03_validity():
    ticks = []
    yaw = 0.0
    for t in range(0, 170):
        if t == 70:
            continue  # tick gap
        static = 101 <= t <= 125
        if t > 0 and not static:
            yaw += 0.125
        ents = {7: ent((0.0, 0.0, 3.0)), 8: ent((0.0, 0.0, 7.0)), 9: ent((1.0, 0.0, 2.0), is_player=False)}
        if t >= 130:
            ents[10] = ent((0.0, 0.0, 2.5))
        attack = {5: 7, 30: 7, 35: 7, 45: 9, 55: 7, 80: 7, 100: 8, 125: 7, 140: 10, 160: 7, 165: 7}.get(t)
        ticks.append(tick(t, yaw, rot_sent=t > 0 and not static, forced=(t == 50), attack=attack, entities=ents))
    expected = {
        "windows": [
            {"anchor_tick": 5, "valid": False, "invalid_reason": "insufficient_history"},
            {"anchor_tick": 30, "valid": True},
            {"anchor_tick": 45, "valid": False, "invalid_reason": "target_not_player"},
            {"anchor_tick": 55, "valid": False, "invalid_reason": "forced_rotation"},
            {"anchor_tick": 80, "valid": False, "invalid_reason": "tick_gap"},
            {"anchor_tick": 100, "valid": False, "invalid_reason": "target_distance"},
            {"anchor_tick": 125, "valid": False, "invalid_reason": "insufficient_path"},
            {"anchor_tick": 140, "valid": False, "invalid_reason": "target_not_tracked"},
            {"anchor_tick": 160, "valid": True},
        ],
        "anchors_skipped_spacing": 2,   # 35 (5 after 30) and 165 (5 after 160)
        "tick_rule_hits": [],
    }
    write(base("A03_validity_and_spacing", "analytic",
               "One session exercising every invalid_reason, plus anchor spacing. Invalid windows must not consume spacing.",
               ticks, expected))


# --------------------------------------------------------------------------- A04
def a04_tick_rules():
    ticks = [tick(t, 0.125 * t, rot_sent=t > 0) for t in range(10)]
    ticks[3]["pitch"] = 91.0
    ticks[4]["pitch"] = 90.0                  # boundary: allowed
    ticks[5]["yaw"] = "NaN"
    ticks[6]["pitch"] = -95.0
    ticks[6]["rot_sent"] = False              # not a client-sent rotation: no rule
    write(base("A04_tick_rules", "analytic", "Tick-scope hard rules: pitch > 90, non-finite rotation; boundary and rot_sent=false cases.",
               ticks, {"windows": [], "anchors_skipped_spacing": 0,
                       "tick_rule_hits": [{"tick": 3, "rule": "HR_PITCH_RANGE"}, {"tick": 5, "rule": "HR_NONFINITE"}]}))


# --------------------------------------------------------------------------- A05/A06
def a05_no_estimate():
    ticks = [tick(t, 6.0 * t, rot_sent=t > 0, attack=7 if t == 30 else None, entities=AHEAD3) for t in range(31)]
    write(base("A05_quant_unavailable_no_estimate", "analytic",
               "6 deg/tick sweep: every delta exceeds accept_max (5.0) so no sensitivity estimate exists; "
               "window is valid and model-scored, but quant_residual_yaw is null.",
               ticks, {"windows": [{"anchor_tick": 30, "valid": True,
                                    "quant_unavailable_reason": "no_sensitivity_estimate",
                                    "features": {"speed_mean": 6.0, "quant_residual_yaw": None}}],
                       "tick_rule_hits": [], "anchors_skipped_spacing": 0, "sensitivity_step_final": None}))


def a06_yaw_precision():
    y0 = 100000.0  # ulp32(1e5) = 0.0078125 > 0.05 * 0.125
    ticks = [tick(t, y0 + 0.125 * t, rot_sent=t > 0, attack=7 if t == 40 else None,
                  entities={7: ent((-3.0 * math.sin(math.radians(y0 + 0.125 * t)), 0.0, 3.0 * math.cos(math.radians(y0 + 0.125 * t))))})
             for t in range(41)]
    assert all(f32(y0 + 0.125 * t) == y0 + 0.125 * t for t in range(41))
    write(base("A06_quant_unavailable_yaw_precision", "analytic",
               "Yaw accumulated near 1e5 deg: binary32 spacing (0.0078) exceeds 5% of the 0.125 step, so the "
               "quantisation channel is not trustworthy and is reported null.",
               ticks, {"windows": [{"anchor_tick": 40, "valid": True, "quant_unavailable_reason": "yaw_precision",
                                    "features": {"quant_residual_yaw": None}}],
                       "tick_rule_hits": [], "anchors_skipped_spacing": 0, "sensitivity_step_final": 0.125}))


# --------------------------------------------------------------------------- R01/R02
def _strafe_session(seed: int, mode: str, n: int = 400):
    """Synthetic stress-test traffic (NOT realistic training data). mode='human': quantised counts,
    ~4-tick reaction lag, noise. mode='lock': un-quantised, lag-0 lock with small float noise."""
    rng = np.random.default_rng(seed)
    step = ((0.5 * 0.6 + 0.2) ** 3) * 8 * 0.15  # slider 0.5 -> 0.15 deg/count
    dist = 2.8
    phase = rng.uniform(0, 2 * math.pi)
    yaw = f32(rng.uniform(-170, 170))
    pitch = f32(5.0)
    centre = yaw
    bearings = []
    ticks = []
    pos = np.array([0.0, 64.0, 0.0])
    for t in range(n):
        b = centre + 25.0 * math.sin(0.11 * t + phase) + 6.0 * math.sin(0.37 * t)
        bearings.append(b)
        bp = 8.0 + 3.0 * math.sin(0.05 * t)
        rel = (-dist * math.sin(math.radians(b)) * math.cos(math.radians(bp)),
               -dist * math.sin(math.radians(bp)),
               dist * math.cos(math.radians(b)) * math.cos(math.radians(bp)))
        if t > 0:
            if mode == "human":
                tgt = bearings[max(t - 4, 0)]
                want = (tgt - yaw) * 0.45 + rng.normal(0, 0.4)
                counts = round(want / step)
                yaw = f32(yaw + f32(counts * step))
                pc = round(((bp - pitch) * 0.3 + rng.normal(0, 0.2)) / step)
                pitch = f32(max(-90.0, min(90.0, pitch + f32(pc * step))))
            else:
                yaw = f32(b + rng.normal(0, 0.05))
                pitch = f32(bp + rng.normal(0, 0.05))
        pos = pos + np.array([0.1 * math.sin(0.2 * t), 0.0, 0.05])
        attack = 7 if (t > 25 and t % 13 == 0) else None
        ticks.append(tick(t, yaw, pitch, rot_sent=t > 0, attack=attack, pos=tuple(pos),
                          ping=float(40 + 10 * math.sin(0.03 * t) + rng.uniform(0, 5)),
                          entities={7: ent(rel)}))
    return ticks


def regression(fid: str, desc: str, ticks):
    fixture = base(fid, "regression", desc, ticks, {})
    fixture["provenance"] = ("synthetic-adversarial-stress-test style generator; expected values FROZEN from the "
                             f"python reference at spec {SPEC_VERSION} (Java-parity only; cannot catch Python bugs)")
    res = extract_session(parse_session(fixture["session"]))
    fixture["expected"] = {
        "windows": [
            {k: v for k, v in w.__dict__.items()} for w in res.windows
        ],
        "tick_rule_hits": res.tick_rule_hits,
        "anchors_skipped_spacing": res.anchors_skipped_spacing,
        "sensitivity_step_final": res.sensitivity_step_final,
    }
    write(fixture)


def main():
    a01_constant_sweep()
    a02_lock(0, "A02_lock_lag0", "Player yaw locked to an orbiting target's bearing with zero lag (aimbot-like): "
             "aim error ~0, track_corr_lag0 = 1, HR_CENTER_LOCK fires when enabled.")
    a02_lock(3, "A02b_follow_lag3", "Player yaw follows the orbiting target's bearing exactly 3 ticks late: "
             "track_corr_lag3 = 1 by construction; HR_CENTER_LOCK must NOT fire.")
    a03_validity()
    a04_tick_rules()
    a05_no_estimate()
    a06_yaw_precision()
    regression("R01_strafe_humanlike", "Seeded synthetic strafe duel, quantised mouse counts with ~4-tick lag.",
               _strafe_session(1, "human"))
    regression("R02_strafe_lock", "Seeded synthetic strafe duel, unquantised lag-0 lock.", _strafe_session(2, "lock"))


if __name__ == "__main__":
    main()
