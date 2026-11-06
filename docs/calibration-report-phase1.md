# Calibration report — Phase 1

## Summary

1. **There's no usable real Minecraft rotation data yet.**
   - The one candidate, the UWEC Minecraft mouse dataset, has no licence.
   - It's also unsuitable on inspection.
   - So nothing in Phase 1 calibrates Minecraft-specific distributions. The only
     trustworthy calibration source will be our own consented capture, which stays
     gated (policy §14).
2. **Instead, we ran a structural check of the feature *definitions* on real, labelled
   human-vs-aimbot data** (GAN-Aimbots, ViZDoom, CC BY 4.0). The features carry modest
   per-window signal, and several design choices are now backed by evidence (below).
3. **The 1.21.x-only constraint has a consequence, as you asked me to flag.** No public
   reference dataset is Minecraft 1.21.x with post-1.9 combat, and none ever was. So the
   version constraint costs us nothing we had. But calibrating the synthetic "legitimate"
   generator (Phase 2) will rest on **untuned priors**, plus whatever the gated test
   server eventually produces.

## 1. Minecraft mouse dataset: why it's unusable

The analysis ran in a scratch area, and nothing was committed.

| Check | Finding |
|---|---|
| Licence | No LICENSE file. The paper's CC BY-SA covers the article only. |
| 10-user "raw" files | Timestamps have **1-second resolution**, so they can't be used at tick scale |
| 40-user raw files | ~8 ms sampling (median dt 8.0 ms) but **absolute desktop cursor X/Y** |
| Is it in-game camera motion? | **No evidence it is.** 0.00% of events are within 2 px of screen centre: Minecraft re-centres or captures the cursor in game, so in-game motion would cluster there. 7.7% of events are pinned at screen edges, which means movement was **clipped** and lost. Coordinates run to −223 / 2113, which suggests multiple monitors. |
| Labels | No in-game vs menu/inventory segmentation |
| Setup | Edition/version unspecified; default sensitivity; Windows pointer acceleration probably on (nonlinear) |

Converting this data to server-side yaw/pitch per tick would require inventing the
missing mapping, which defeats the point of calibrating against it.

## 2. GAN-Aimbots structural check

Script: `ml/calibration/gan_aimbots_structural.py`. Reproduce with
`FMAC_DATA_ROOT=… python -I ml/calibration/gan_aimbots_structural.py`.

### Setup

- **Data:** collections 1 and 2. That's 16,468 shot-anchored 1-second windows from
  26 recording machines: human 8,163; light 2,700; strong 2,537; GAN-1 1,086;
  GAN-2 982.
- **Features:** the spec's formulas, mapped to ViZDoom:
  - 35-frame windows
  - "lag 3 ticks" → lag 5 frames
  - aim error from screen-space boxes
- **Alignment:** action → render lag of 0 frames, chosen because it made the target's
  world-bearing smoothest on human data.
- **Metric:** separation = max(AUC, 1−AUC), window-level. "+" means the aimbot's value is
  higher.

| Feature | light | strong | GAN-1 | GAN-2 |
|---|---|---|---|---|
| `speed_mean` | 0.59+ | 0.60+ | 0.54+ | 0.59+ |
| `speed_max` | 0.51− | 0.60− | 0.54− | 0.51− |
| `accel_mean` | 0.60+ | 0.59+ | 0.56− | 0.56− |
| `jitter_ratio` | 0.58+ | 0.61+ | **0.72−** | **0.73−** |
| `path_straightness` | 0.50 | 0.52 | 0.53 | 0.52 |
| `pitch_share` | 0.85+ | 0.92+ | 0.76+ | 0.79+ |
| `aim_err_attack` | 0.66− | 0.79− | 0.62− | 0.65− |
| `aim_err_track_mean` | 0.65− | **0.85−** | 0.67− | 0.72− |
| `aim_err_track_std` | 0.60− | 0.81− | 0.64− | 0.69− |
| `track_corr_lag0` | 0.65+ | **0.81+** | 0.63+ | 0.69+ |
| `track_corr_lag(150 ms)` | 0.60+ | 0.68+ | 0.59+ | 0.66+ |
| `quant_residual` | 0.50 | 0.50 | 0.50 | 0.50 |

### What this supports

- **Evidence must accumulate across windows.** Per-window separation is 0.6–0.85, so a
  single window can't justify a flag. This supports the sequential Yellow-Flag design.
- **The density model needs to flag in both directions.** GAN aimbots have *lower*
  jitter than humans, while light/strong have *higher*. A one-sided rule ("flag high
  jitter") would miss one family, and a density model doesn't.
- **The correlation-based reaction-time replacement works.** `track_corr_lag0` is the
  most consistent behavioural signal across all four aimbot types.
- **The quantisation residual is useless against cheats that quantise** (AUC 0.50). That
  backs ADR 0001's decision to keep it out of the model input.

### Caveats (don't over-read this)

- **`pitch_share` is probably a Doom artifact.** Doom play rarely uses pitch, and the
  aimbots adjust it. Minecraft PvP uses pitch constantly, so this must **not** be read
  as evidence that `pitch_share` works in Minecraft.
- **`path_straightness` and `speed_max` showed ~no signal.** They're candidates for
  removal in Phase 2, but only once Minecraft data says so too.
- **The screen-space bearing approximation inflates lag-0 correlation for everyone.**
  It uses the authors' linear pixel→degree convention, so part of the player's own
  rotation leaks into the target's "bearing". The human median is 0.47. The Minecraft
  spec computes bearing from 3D vectors and doesn't have this leak.
- **Windows aren't independent**, because the same players appear many times. AUCs are
  descriptive, not test statistics.
- **It's a different game, rate, field of view and weapon set.** Feature **values** and
  thresholds don't transfer, only the qualitative conclusions above.
- **These are assist aimbots from 2019–2021 research code.** Real Minecraft clients
  (Phase 3) may behave differently.
