# ADR 0004 — Licensing constraints

- **Status:** Accepted
- **Date:** 2026-10-15

The repository and model weights are **private** for now. These constraints are
tracked anyway, in case that changes.

| Component | Licence | Consequence |
|---|---|---|
| PacketEvents (plugin dependency) | GPL-3.0 | `/plugin` links it, so it is effectively **GPL-3.0**. If it's ever distributed, its source has to go with it. |
| Grim | GPL-3.0 | Treated as **black-box only**: we run it next to our plugin and read its violation logs. We read `AimProcessor`, `AimDuplicateLook` and `AimModulo360` to confirm protocol facts (the sensitivity formula) and to understand what the baseline does. **No code was copied.** Any future code reuse makes the consumer GPL-3.0. |
| XGuardian artifacts | GPL-3.0-or-later (Zenodo) | Using the data for calibration or evaluation is fine. Any reuse of its code would be GPL. |
| GAN-Aimbots data | CC BY 4.0 | Attribution is required in any publication or report that uses results derived from it. |
| GAN-Aimbots code | MIT | Read for action indices and the screen convention. Not vendored. |
| Minecraft mouse-dynamics dataset | **No licence found** | Not used (and unsuitable anyway; see the calibration report). |
| DJL / ONNX Runtime | Apache-2.0 / MIT | Compatible with GPL-3.0. |
| `/ml`, `/schema`, `/eval` | Project's own | Kept free of GPL code so they stay independent of the plugin's GPL obligations. **Don't import from `/plugin`.** |

There's also a Mojang/Microsoft question: whether the Minecraft EULA and Usage
Guidelines allow a server to collect telemetry. It's in the privacy policy (§15) for
legal review.
