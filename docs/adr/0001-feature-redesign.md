# ADR 0001 — Feature redesign against what the server can actually observe

- **Status:** Accepted (Phase 1). Spec: `schema/features.yaml` v1.0.0
- **Date:** 2026-10-15

## Context

The hackathon prototype used 10 engineered features. The consolidated notes name six of
them: velocity, acceleration, jitter, path ratio, reaction time, flick angle. The other
four were never written down, so this ADR can't classify them. All ten were designed as
if the server could see continuous mouse telemetry. It can't.

What a 1.21.2+ Paper server actually observes:

- **One absolute yaw/pitch per client tick (20 Hz).** These are binary32 floats sent in
  movement packets. Tick boundaries are known exactly from `CLIENT_TICK_END`, which was
  added in 1.21.2 and is why 1.21.0 and 1.21.1 are excluded.
- **No sub-tick dynamics.** Physiological tremor (8–12 Hz) is at or above the 10 Hz
  Nyquist limit, so it's aliased. Anything shorter than 50 ms is invisible.
- **Rotation is quantised.** The vanilla client turns by `counts × step`, where
  `step = ((0.6·s + 0.2)³ · 8) · 0.15` degrees and `s ∈ [0,1]` is the sensitivity
  slider. This is the source of the "GCD" checks used by existing anticheats; we
  confirmed the formula against Grim's `AimProcessor` by reading it only, without
  copying code.
- **Packet arrival timing reflects the network more than the player.** It's used only
  as context (ping), never as a behavioural feature.
- **Where the target is depends on lag compensation.** The client sees a *predicted,
  interpolated* target position, not the server's. The tick record therefore carries
  client-perceived relative positions, and computing them is the job of the Phase 4
  capture layer (ADR 0002).

## Decision — feature by feature

| Original feature | Status | New feature(s) | Why |
|---|---|---|---|
| velocity | **Redefined** | `speed_mean` | Per-tick mouse-space speed (°/tick), not a continuous velocity |
| flick angle | **Redefined** | `speed_max` | A flick can only be measured as the largest single-tick rotation |
| acceleration | **Redefined** | `accel_mean` | Mean change in the per-tick rotation vector. Heavily aliased at 20 Hz |
| jitter | **Redefined** | `jitter_ratio` | Physiological tremor is invisible. This measures tick-scale micro-corrections instead: deviation from a 3-tick moving average, divided by path length |
| path ratio | **Kept** | `path_straightness` | Net displacement ÷ path length. Same idea at tick resolution |
| reaction time | **Dropped, replaced** | `track_corr_lag0`, `track_corr_lag3` | Stimulus onset on the client's screen is unknowable and one tick is 50 ms. Replaced by how the player's yaw changes correlate with the target's bearing changes, at lag 0 and at lag 3 ticks (≈150 ms, a typical human response delay) |
| *(4 unnamed)* | Unknown | — | Never specified in the source document |
| — | **New** | `pitch_share` | Share of rotation that is vertical; simple aimbots are often yaw-only |
| — | **New** | `aim_err_attack`, `aim_err_track_mean`, `aim_err_track_std` | Angular error to the target hitbox centre, in units of hitbox angular radius, at the attack and over the window |
| — | **New, auxiliary** | `quant_residual_yaw` | How far yaw deltas are from integer multiples of the estimated step. **Not a model input** (see below) |

## Context (conditioning) variables

| Original | Status | New | Why |
|---|---|---|---|
| weapon | Kept | `weapon_class` | Main-hand item class at the attack. Melee only in v1; bows don't produce attack packets |
| distance | Kept | `target_distance` | Client-perceived distance at the attack |
| situation | Redefined | `target_ang_speed`, `self_speed` | Replaced by measurable difficulty drivers: how fast the target moves across the view, and how fast the player strafes |
| — | New | `ping_ms` | Latency changes what the client saw and how hard lag compensation is |
| **skill** | **Dropped** | — | **Circular.** Skill isn't observable, and estimating it from the player's own aim means conditioning on the thing being tested: a cheater would raise their own "skill" and widen their own normal band. Only revisit with an aim-independent signal |

## Hard rules

| Original rule | Status | Replacement |
|---|---|---|
| rotation > 100°/ms | **Dropped** | Can't be measured at tick resolution, and a legitimate flick can exceed 180° in one tick |
| reaction < 50 ms | **Dropped** | Can't be measured: one tick, plus network jitter |
| — | New | `HR_PITCH_RANGE` (\|pitch\| > 90°) and `HR_NONFINITE`. Both are impossible from a vanilla client |
| — | New, **disabled** | `HR_CENTER_LOCK`: crosshair held on the hitbox centre for 8+ ticks while the target moves >1°/tick. Stays off until Phase 3 measures its false-positive rate (CT-02) |

Rule hits are only **evidence for the Yellow-Flag accumulator**. They never trigger an
action on their own.

## Why `quant_residual_yaw` is not a model input

In the first draft, a window without a sensitivity estimate was "model-unscorable".
The R02 regression fixture (an unquantised lock-on aimbot) showed this would leave the
most blatant cheat **completely unscored**: its rotations never fit a GCD, so no
estimate ever forms.

Quantisation was therefore moved to an auxiliary channel, and the flow model scores
every valid window on the other 11 features. The GAN-Aimbots structural check
(docs/calibration-report-phase1.md) adds a second reason. When cheat output is
quantised, as with Minecraft cheats that use a "GCD fix", the residual carries
**zero** signal (AUC 0.50). So it only catches naive cheats, and shouldn't shape the
density model.

## Consequences and known weaknesses

- **The doc's §5 claim that "the data is cleanly continuous" is only partly true.**
  Per-tick deltas are discrete (integer counts × step). Features like `jitter_ratio`
  and the correlations have point masses: a correlation is exactly 0 when the target
  is stationary. Phase 2 has to handle this with dequantisation noise or explicit
  mixture components, or the flow's densities near those points are meaningless.
- **Lag-compensation quality caps every aim-error feature.** A biased reconstruction
  looks like bad aim, which lowers scores, so the failure is safe for false positives
  but loses detection.
- **Single modality** (rotation only) is still a known limitation, as in the original
  §14.
- The 20-tick window and 10-tick anchor spacing are untuned defaults. They get revisited
  only with real data.
