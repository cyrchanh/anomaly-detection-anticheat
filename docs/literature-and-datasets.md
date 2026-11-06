# Literature & dataset survey (Phase 1)

Verified 2026-10-15. "Verified" means we read the primary source (arXiv page, Zenodo
record, or repository), not a summary of it.

## Datasets

| Dataset | Game / rate | Licence (verified?) | Usable? | Role |
|---|---|---|---|---|
| **GAN-Aimbots** (Kanervisto, Kinnunen, Hautamäki; [Zenodo 6345323](https://zenodo.org/record/6345323)) | ViZDoom, 35 fps; per-frame yaw/pitch deltas (quantised to 360/2048°), screen-space enemy boxes, per-game labels: none / light / strong / GAN×2 | **CC BY 4.0** (yes) | **Yes**, as a structural reference only | Phase 1 structural check of feature *definitions*; Phase 3 cross-game sanity check. ⚠️ Files contain `hwid` = the recording machine's MAC address. Our code never reads it. |
| **XGuardian** (Zhang, Sun, Qian, USENIX Sec '26; [Zenodo 17845614](https://zenodo.org/doi/10.5281/zenodo.17845614)) | CS2 ~64 tick/s (+ Farlight84); 31,971 trajectories, 5,486 players, manually re-verified labels | **GPL-3.0-or-later** (yes, Zenodo record) | Yes. **Not downloaded** (22 GB + 13 parts) | Methodology reference. Possible Phase 3 cross-check on request. |
| **Minecraft Mouse Dynamics** (Siddiqui, Dave, Seliya; [GitHub](https://github.com/NyleSiddiqui/Minecraft-Mouse-Dynamics-Dataset)) | Minecraft, edition unknown ("free trial"), desktop cursor events | **No licence file** (yes; default all-rights-reserved) | **No** | Blocked twice over, by licence and by unsuitability. See the calibration report. |
| **CS2CD** (AntiCheatPT, [arXiv:2508.06348](https://arxiv.org/abs/2508.06348)) | CS2, 795 matches | Unknown (hosting URL not found) | No, until the licence is found | — |

## Papers checked

| Claim in brief / notes | Verified result |
|---|---|
| arXiv:2110.11080 is a Minecraft mouse dataset, 10 users × 20 min | **True.** There's also a 40-user follow-up (MDPI MAKE) in the same repo. Data is cursor X/Y, not raw mouse counts. |
| XGuardian (arXiv:2601.18068) is server-side, pitch/yaw only, public dataset | **True.** Features are velocity, acceleration and angular change, fed to a GRU-CNN with SHAP explanations. Reports FPR 0.062. Its "evasion" set (cheaters with at least one feature within ±10% of the human mean) kept 0.818 recall. **Note:** they assume cheaters who fully mimic humans lose their advantage. That's an argument, not a guarantee. |
| "YAACS" paper and "GAN-Aimbots approach" | **YAACS exists:** Dhinge et al., "Server-side Anti-cheat in FPS games for Aimbot detection…", [arXiv:2607.04336](https://arxiv.org/abs/2607.04336) (Jul 2026). Stacked LSTM, 88.6% acc / 0.97% FPR. **Game unnamed, cheat-generation method not described, no data or code release found, no mention of GAN-Aimbots.** The brief linked YAACS to GAN-Aimbots; **that link isn't supported**, since GAN-Aimbots is the separate Kanervisto et al. work. YAACS isn't relied on for anything. |
| GAN-Aimbots as a hard-negative generator | **True** ([arXiv:2205.07060](https://arxiv.org/abs/2205.07060), IEEE ToG). Code is MIT, data is CC BY 4.0. Judged by humans and automatic detectors as hard to detect. |
| Related, new: "Aim Low, Shoot High" (Witschel & Wressnegger, EuroSec 2020) | Adaptive aimbot that copies a user's profile and slowly raises performance. Evaded two open-source ACs plus VAC/VACnet/Overwatch in a CS:GO study. PoC code at github.com/intellisec/aimbot (**licence not stated**). This is the threat model for "slow-drift" cheats: **per-player baselines are themselves attackable.** |

The references in the original notes (Lipman et al. flow matching; Kirichenko et al.
OOD failure; InFlow; etc.) were not re-verified one by one in Phase 1. The core
flow-matching papers (2210.02747, 2412.06264) will be checked in Phase 2, before
they're relied on for the training code.

## Baseline anticheat: what Grim actually checks (read, not copied)

Grim's open-source aim checks are limited to:

- `AimProcessor`: a sensitivity/GCD estimator, which isn't a check by itself
- `AimDuplicateLook`: an identical rotation packet with no change
- `AimModulo360`: a single-tick yaw snap over 320° from a small previous delta

Its combat checks (`Reach`, `Hitboxes`, `MultiInteract*`, `InvalidInteract*`) target
reach and killaura **geometry**, not aim **behaviour**.

**Consequence for Phase 3:** "beats Grim at aim detection" is a very low bar. Open-source
Grim barely tries to detect humanised aim assist. The comparison stays mandatory, as
the brief requires. But Phase 3 will also add a simple non-ML statistical baseline
(per-feature robust z-scores plus the sequential accumulator), so flow matching has to
beat something that actually attempts the same task.

## Open-source cheat clients (Phase 3 cheat-side data)

Wurst, Meteor and LiquidBounce were approved, open-source only, run in an isolated VM.
Their aim modules are still to be inventoried in Phase 3 against our 1.21.2+ floor.
Based on general knowledge, **not yet verified**, these clients ship killaura and
aim-assist modules with rotation-speed and randomisation settings. A
learned-humanisation aimbot like GAN-Aimbot is likely **not** among them. As agreed,
that gap is filled by our own GAN-Aimbot-style hard-negative generator, not by a
closed-source client.
