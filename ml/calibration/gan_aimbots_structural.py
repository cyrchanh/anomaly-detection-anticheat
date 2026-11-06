"""Structural check of the FMAC feature DEFINITIONS on real, labelled human-vs-aimbot data.

Dataset: GAN-Aimbots (Kanervisto et al., CC BY 4.0), ViZDoom at 35 frames/s.
This is NOT Minecraft and NOT calibration of Minecraft distributions. It answers one
question: on real consenting humans, at a tick-sampled rate comparable to Minecraft's
20 Hz, do the spec's feature *formulas* carry any signal against assist-style aimbots?

Mapping to the Minecraft spec (documented in docs/calibration-report-phase1.md):
  * window = 1 s  (35 frames here, 20 ticks in Minecraft)
  * track_corr "lag3" (150 ms at 20 Hz)  ->  lag 5 frames (143 ms at 35 Hz)
  * aim error: screen-space bbox centre offset from crosshair, in degrees using the
    dataset authors' own linear pixel->degree convention, normalised by bbox half-width
  * quantisation: ViZDoom mouse deltas are multiples of 360/2048 deg (cf. Minecraft GCD)
  * anchor = a shot (ammo decrease), same rule as the authors' feature_extraction.py
The `hwid` field (a MAC address) is never read.

Usage:  FMAC_DATA_ROOT=... python ml/calibration/gan_aimbots_structural.py [--out results.json]
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
from collections import defaultdict
from pathlib import Path

import numpy as np

FPS = 35
W = 35                      # 1 second of frames
LAG_HUMAN = 5               # ~143 ms, the 35 Hz analogue of 3 ticks at 20 Hz
WIDTH, HEIGHT = 640, 480
CROSS_X, CROSS_Y = 320, 201
FOVX = 90.0
FOVY = FOVX * (WIDTH / HEIGHT)   # authors' convention (recording.py); kept for consistency
YAW_IDX, PITCH_IDX = 4, 5
QUANT = 360.0 / 2048.0
SKIP_WEAPONS = {5, 6}
AMMO_PER_SHOT = {1: 1, 2: 1, 3: 2, 4: 1, 5: 1, 6: 1}
LABELS = {None: "human", "ease_light": "light", "ease_strong": "strong", "gan_group0": "gan1", "gan_group1": "gan2"}

FEATURES = ["speed_mean", "speed_max", "accel_mean", "jitter_ratio", "path_straightness", "pitch_share",
            "aim_err_attack", "aim_err_track_mean", "aim_err_track_std", "track_corr_lag0", "track_corr_lagH",
            "quant_residual"]


def pearson(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.std() < 1e-9 or y.std() < 1e-9:
        return 0.0
    return float(((x - x.mean()) * (y - y.mean())).mean() / (x.std() * y.std()))


def shots(ep):
    out, last = [], None
    for i in range(1, len(ep["ammos"])):
        w = int(ep["weapons"][i])
        if w in SKIP_WEAPONS:
            last = None
            continue
        a = ep["ammos"][i]
        if last is not None and last - a == AMMO_PER_SHOT.get(w, 1):
            out.append(i)
        last = a
    return out


def track_target(bbs, start, end):
    """Nearest-neighbour track of the bbox closest to the crosshair at `end`, backwards to `start`."""
    cur = bbs[end]
    if not cur:
        return None
    pick = min(cur, key=lambda b: ((b[0] + b[2]) / 2 - CROSS_X) ** 2 + ((b[1] + b[3]) / 2 - CROSS_Y) ** 2)
    seq = [pick]
    for t in range(end - 1, start - 1, -1):
        if not bbs[t]:
            return None
        px, py = (seq[-1][0] + seq[-1][2]) / 2, (seq[-1][1] + seq[-1][3]) / 2
        nb = min(bbs[t], key=lambda b: ((b[0] + b[2]) / 2 - px) ** 2 + ((b[1] + b[3]) / 2 - py) ** 2)
        if abs((nb[0] + nb[2]) / 2 - px) > 80:     # lost track
            return None
        seq.append(nb)
    return seq[::-1]


def window_features(dy, dp, boxes, view_lag):
    """dy/dp: W+1 deltas aligned with boxes (index 0 unused). view_lag: frames between an action and its effect on the rendered view."""
    dy, dp = np.asarray(dy[1:], float), np.asarray(dp[1:], float)
    s = np.sqrt(dy ** 2 + dp ** 2)
    if s.sum() < 1.0:
        return None
    cx = np.array([(b[0] + b[2]) / 2 for b in boxes], float)
    cy = np.array([(b[1] + b[3]) / 2 for b in boxes], float)
    hw = np.array([max((b[2] - b[0]) / 2, 1.0) for b in boxes], float)
    ax = (cx - CROSS_X) / WIDTH * FOVX
    ay = (cy - CROSS_Y) / HEIGHT * FOVY
    e = np.sqrt(ax ** 2 + ay ** 2) / (hw / WIDTH * FOVX)
    yaw = np.concatenate([[0.0], np.cumsum(dy)])
    yaw_view = np.concatenate([np.zeros(view_lag), yaw[:len(yaw) - view_lag]]) if view_lag else yaw
    bearing = yaw_view + ax
    x = np.diff(bearing)
    jit_num = sum(math.hypot(dy[i] - (dy[i - 1] + dy[i] + dy[i + 1]) / 3, dp[i] - (dp[i - 1] + dp[i] + dp[i + 1]) / 3)
                  for i in range(1, len(dy) - 1))
    jit_den = s[1:-1].sum()
    nz = np.abs(dy[dy != 0]) / QUANT
    return {
        "speed_mean": s.mean(), "speed_max": s.max(),
        "accel_mean": np.sqrt(np.diff(dy) ** 2 + np.diff(dp) ** 2).mean(),
        "jitter_ratio": jit_num / jit_den if jit_den >= 1e-9 else 0.0,
        "path_straightness": math.hypot(dy.sum(), dp.sum()) / s.sum(),
        "pitch_share": np.abs(dp).sum() / (np.abs(dy).sum() + np.abs(dp).sum()),
        "aim_err_attack": e[-1], "aim_err_track_mean": e.mean(), "aim_err_track_std": e.std(),
        "track_corr_lag0": pearson(x, dy), "track_corr_lagH": pearson(x[:-LAG_HUMAN], dy[LAG_HUMAN:]),
        "quant_residual": float(np.abs(nz - np.floor(nz + 0.5)).mean()) if len(nz) else 0.0,
    }


def auc(pos, neg):
    """P(score_pos > score_neg) via Mann-Whitney U, ties counted half."""
    pos, neg = np.asarray(pos), np.asarray(neg)
    allv = np.concatenate([pos, neg])
    ranks = allv.argsort().argsort().astype(float) + 1
    # average ranks for ties
    order = np.sort(allv)
    _, inv, counts = np.unique(allv, return_inverse=True, return_counts=True)
    cum = np.cumsum(counts)
    avg = cum - (counts - 1) / 2.0
    ranks = avg[inv]
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def choose_view_lag(episodes):
    """Pick the action->render alignment that makes target world-bearing smoothest on HUMAN data."""
    scores = {}
    for lag in (0, 1, 2):
        v = []
        for ep, label in episodes:
            if label != "human":
                continue
            dy = ep["actions_dy"]
            for sh in shots(ep)[:40]:
                st = sh - W
                if st < 1:
                    continue
                seq = track_target(ep["enemy_bbs"], st, sh)
                if seq is None:
                    continue
                ax = np.array([((b[0] + b[2]) / 2 - CROSS_X) / WIDTH * FOVX for b in seq])
                yaw = np.concatenate([[0.0], np.cumsum(dy[st + 1: sh + 1])])
                yv = np.concatenate([np.zeros(lag), yaw[:len(yaw) - lag]]) if lag else yaw
                v.append(np.var(np.diff(yv + ax)))
        scores[lag] = float(np.median(v)) if v else math.inf
    return min(scores, key=scores.get), scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    root = Path(os.environ["FMAC_DATA_ROOT"]) / "public-reference" / "gan-aimbots"
    files = sorted(glob.glob(str(root / "data_collection_1" / "*.json")) + glob.glob(str(root / "data_collection_2" / "*.json")))
    episodes = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            d = json.load(fh)
        ep = {k: d[k] for k in ("ammos", "weapons", "enemy_bbs")}
        ep["actions_dy"] = [a[YAW_IDX] for a in d["actions"]]
        ep["actions_dp"] = [a[PITCH_IDX] for a in d["actions"]]
        ep["player"] = Path(f).name.split("_")[1]   # recording-machine id prefix, used only to count players
        episodes.append((ep, LABELS[d["aimbot"]]))

    view_lag, lag_scores = choose_view_lag(episodes)
    rows = defaultdict(list)
    players = defaultdict(set)
    for ep, label in episodes:
        for sh in shots(ep):
            st = sh - W
            if st < 1:
                continue
            seq = track_target(ep["enemy_bbs"], st, sh)
            if seq is None:
                continue
            f = window_features(ep["actions_dy"][st: sh + 1], ep["actions_dp"][st: sh + 1], seq, view_lag)
            if f is None:
                continue
            rows[label].append(f)
            players[label].add(ep["player"])

    result = {"view_lag_frames": view_lag, "view_lag_scores": lag_scores,
              "windows": {k: len(v) for k, v in rows.items()},
              "recording_machines": {k: len(v) for k, v in players.items()},
              "medians": {}, "auc_vs_human": {}}
    for label, rs in rows.items():
        result["medians"][label] = {f: float(np.median([r[f] for r in rs])) for f in FEATURES}
    human = rows["human"]
    for label, rs in rows.items():
        if label == "human":
            continue
        result["auc_vs_human"][label] = {f: auc([r[f] for r in rs], [r[f] for r in human]) for f in FEATURES}
    text = json.dumps(result, indent=1)
    print(text)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
