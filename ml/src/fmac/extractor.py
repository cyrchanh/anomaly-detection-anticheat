"""Stage B reference extractor: TickRecords -> FeatureWindows + rule hits.

Normative spec: schema/features.yaml. This module is deliberately plain Python
(no numpy) so each line maps 1:1 onto the Java port and onto the spec prose.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from fmac.geometry import bearing, hyp, norm3, normalised_aim_error, ulp32, wrap180
from fmac.records import TickRecord
from fmac.sensitivity import SensitivityEstimator
from fmac.spec import load_spec


@dataclass
class FeatureWindow:
    anchor_tick: int
    target_id: int
    valid: bool
    invalid_reason: str | None = None
    quant_unavailable_reason: str | None = None
    features: dict[str, float | None] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    rule_hits: list[str] = field(default_factory=list)


@dataclass
class SessionResult:
    windows: list[FeatureWindow]
    tick_rule_hits: list[dict[str, Any]]
    anchors_skipped_spacing: int
    sensitivity_step_final: float | None


def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    vx = sum((x - mx) ** 2 for x in xs) / n
    vy = sum((y - my) ** 2 for y in ys) / n
    if math.sqrt(vx) < 1e-9 or math.sqrt(vy) < 1e-9:
        return 0.0
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    return cov / math.sqrt(vx * vy)


def _tick_rules(r: TickRecord, rules: list[dict[str, Any]]) -> list[str]:
    if not r.rot_sent:
        return []
    hits = []
    enabled = {s["id"] for s in rules if s["scope"] == "tick" and s["enabled"]}
    finite = math.isfinite(r.yaw) and math.isfinite(r.pitch)
    if "HR_NONFINITE" in enabled and not finite:
        hits.append("HR_NONFINITE")
    if "HR_PITCH_RANGE" in enabled and math.isfinite(r.pitch) and abs(r.pitch) > 90.0:
        hits.append("HR_PITCH_RANGE")
    return hits


def _check_validity(recs: list[TickRecord], idx: int, target: int, cfg: dict[str, Any]) -> tuple[str | None, list[TickRecord]]:
    W = cfg["length_deltas"]
    anchor = recs[idx]
    ent = anchor.entities.get(target)
    if ent is None or not ent.is_player:
        return "target_not_player", []
    if idx < W:
        return "insufficient_history", []
    win = recs[idx - W: idx + 1]
    if any(win[i].tick != win[0].tick + i for i in range(W + 1)):
        return "tick_gap", win
    if any(r.forced_rotation for r in win):
        return "forced_rotation", win
    if any(not (math.isfinite(r.yaw) and math.isfinite(r.pitch)) for r in win):
        return "non_finite_rotation", win
    if any(target not in r.entities for r in win):
        return "target_not_tracked", win
    lo, hi = cfg["target_distance_range"]
    if not (lo <= norm3(ent.rel) <= hi):
        return "target_distance", win
    path = sum(hyp(win[i].yaw - win[i - 1].yaw, win[i].pitch - win[i - 1].pitch) for i in range(1, W + 1))
    if path < cfg["min_path_deg"]:
        return "insufficient_path", win
    return None, win


def _window_features(win: list[TickRecord], target: int, step: float | None, cfg: dict[str, Any],
                     rules: list[dict[str, Any]]) -> FeatureWindow:
    W = cfg["length_deltas"]
    anchor = win[-1]
    fw = FeatureWindow(anchor_tick=anchor.tick, target_id=target, valid=True)

    dy = [0.0] + [win[i].yaw - win[i - 1].yaw for i in range(1, W + 1)]
    dp = [0.0] + [win[i].pitch - win[i - 1].pitch for i in range(1, W + 1)]
    s = [0.0] + [math.sqrt(dy[i] ** 2 + dp[i] ** 2) for i in range(1, W + 1)]
    ents = [r.entities[target] for r in win]
    e = [normalised_aim_error(win[i].yaw, win[i].pitch, ents[i].rel, ents[i].half_width) for i in range(W + 1)]
    b = [bearing(ent.rel) for ent in ents]
    x = [0.0] + [wrap180(b[i][0] - b[i - 1][0]) for i in range(1, W + 1)]
    bp = [0.0] + [b[i][1] - b[i - 1][1] for i in range(1, W + 1)]
    tgt_speed = [0.0] + [math.sqrt(x[i] ** 2 + bp[i] ** 2) for i in range(1, W + 1)]

    sum_s = sum(s[1:])
    f: dict[str, float | None] = {}
    f["speed_mean"] = sum_s / W
    f["speed_max"] = max(s[1:])
    f["accel_mean"] = sum(hyp(dy[i] - dy[i - 1], dp[i] - dp[i - 1]) for i in range(2, W + 1)) / (W - 1)

    num = den = 0.0
    for i in range(2, W):
        my = (dy[i - 1] + dy[i] + dy[i + 1]) / 3.0
        mp = (dp[i - 1] + dp[i] + dp[i + 1]) / 3.0
        num += hyp(dy[i] - my, dp[i] - mp)
        den += s[i]
    f["jitter_ratio"] = 0.0 if den < 1e-9 else num / den

    f["path_straightness"] = hyp(sum(dy[1:]), sum(dp[1:])) / sum_s
    sum_ady = sum(abs(v) for v in dy[1:])
    sum_adp = sum(abs(v) for v in dp[1:])
    f["pitch_share"] = sum_adp / (sum_ady + sum_adp)

    f["aim_err_attack"] = e[W]
    mean_e = sum(e) / (W + 1)
    f["aim_err_track_mean"] = mean_e
    f["aim_err_track_std"] = math.sqrt(sum((v - mean_e) ** 2 for v in e) / (W + 1))

    f["track_corr_lag0"] = _pearson(x[1:], dy[1:])
    f["track_corr_lag3"] = _pearson([x[i - 3] for i in range(4, W + 1)], dy[4:])

    max_abs_yaw = max(abs(r.yaw) for r in win)
    if step is None:
        fw.quant_unavailable_reason = "no_sensitivity_estimate"
    elif ulp32(max_abs_yaw) > cfg["max_yaw_ulp_to_step_ratio"] * step:
        fw.quant_unavailable_reason = "yaw_precision"
    if fw.quant_unavailable_reason is None:
        res = []
        for v in dy[1:]:
            if v != 0.0:
                q = abs(v) / step
                res.append(abs(q - math.floor(q + 0.5)))
        f["quant_residual_yaw"] = sum(res) / len(res) if res else 0.0
    else:
        f["quant_residual_yaw"] = None
    fw.features = f

    pings = sorted(r.ping_ms for r in win)
    fw.context = {
        "weapon_class": anchor.held_item,
        "target_distance": norm3(ents[W].rel),
        "target_ang_speed": sum(tgt_speed[1:]) / W,
        "self_speed": sum(hyp(win[i].self_pos[0] - win[i - 1].self_pos[0],
                                     win[i].self_pos[2] - win[i - 1].self_pos[2]) for i in range(1, W + 1)) / W,
        "ping_ms": pings[len(pings) // 2],
    }

    for rule in rules:
        if rule["scope"] != "window" or not rule["enabled"]:
            continue
        if rule["id"] == "HR_CENTER_LOCK":
            p = rule["params"]
            run = best = 0
            for i in range(1, W + 1):
                if e[i] < p["max_norm_err"] and tgt_speed[i] > p["min_target_ang_speed"]:
                    run += 1
                    best = max(best, run)
                else:
                    run = 0
            if best >= p["min_run_ticks"]:
                fw.rule_hits.append("HR_CENTER_LOCK")
    return fw


def extract_session(recs: list[TickRecord], rule_overrides: dict[str, bool] | None = None) -> SessionResult:
    """Run Stage B over a whole session.

    rule_overrides lets tests/eval force a rule on or off without editing the
    spec; production code never passes it.
    """
    spec = load_spec()
    cfg = spec["window"]
    rules = [dict(r, enabled=rule_overrides.get(r["id"], r["enabled"])) if rule_overrides else r
             for r in spec["rules"]]
    est = SensitivityEstimator()
    windows: list[FeatureWindow] = []
    tick_hits: list[dict[str, Any]] = []
    skipped = 0
    last_valid_anchor: int | None = None

    for idx, r in enumerate(recs):
        est.update(recs[idx - 1] if idx > 0 else None, r)
        for h in _tick_rules(r, rules):
            tick_hits.append({"tick": r.tick, "rule": h})
        if r.attack_target is None:
            continue
        if last_valid_anchor is not None and r.tick - last_valid_anchor < cfg["min_anchor_spacing_ticks"]:
            skipped += 1
            continue
        reason, win = _check_validity(recs, idx, r.attack_target, cfg)
        if reason is not None:
            windows.append(FeatureWindow(anchor_tick=r.tick, target_id=r.attack_target, valid=False, invalid_reason=reason))
            continue
        windows.append(_window_features(win, r.attack_target, est.estimate(), cfg, rules))
        last_valid_anchor = r.tick
    final_step = est.estimate()
    return SessionResult(windows, tick_hits, skipped, final_step)
