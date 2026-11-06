# Risk register

Carried over from the original notes (§14), plus everything surfaced since.
Status: **Open / Mitigated / Accepted / Monitoring**.

| # | Risk | Impact | Mitigation / owner phase | Status |
|---|---|---|---|---|
| R1 | Synthetic-data circularity: the original 96.3% "accuracy" measured a separation we built into the data ourselves | Overclaiming | The synthetic generator is relabelled a stress-test tool. `provenance.mix()` forbids synthetic data in `eval-legit`, so no false-positive claim can rest on synthetic data. | Mitigated (process) |
| R2 | No real Minecraft calibration data exists publicly | The synthetic "legitimate" generator rests on priors | Calibration report §1. Gated consented capture is the only real fix. | Open |
| R3 | Training-serving skew | Silent accuracy loss | ADR 0002: two-stage contract, spec-loaded constants, shared fixtures in CI on both sides | Mitigated for Stage B. Stage A open (Phase 4) |
| R4 | Lag-compensation error in client-perceived target positions | Aim-error features become noisy or biased | Phase 4 capture layer, validated against a client-side ground truth logger on the test server | Open |
| R5 | Likelihood ≠ semantic anomaly (Kirichenko et al.) | Confidently wrong scores | Compare against simple density baselines; inspect which features drive each score in the review UI | Open (Phase 2–3) |
| R6 | Subtle / humanised cheats sit inside the human distribution | Missed detections | GAN-style hard-negative generator (Phase 2); sequential accumulation. Per-window separation of 0.6–0.7 against light/GAN aimbots (calibration report) shows how hard this is. | Open, **headline risk** |
| R7 | Adaptive adversary tunes their cheat to the thresholds | Arms race | Repo and weights are private; no score oracle reaches the client; thresholds aren't static. This can never be fully mitigated. | Accepted, **headline risk** |
| R8 | Adaptive *slow-drift* cheats (Witschel & Wressnegger 2020) game per-player baselines | Undetected gradual cheating | Don't use per-player baselines as the only reference; keep population conditioning | Open |
| R9 | Training data poisoning: "presumed legitimate" data contains cheaters, or an attacker deliberately poisons retraining | The model learns cheating as normal | Clean sessions using Grim flags and bans; no automatic online retraining; retraining is a reviewed batch step | Open (Phase 2/4) |
| R10 | Point masses in discrete features break flow densities | Meaningless likelihoods | Dequantisation or mixture handling (ADR 0001) | Open (Phase 2) |
| R11 | Most blatant cheat (un-quantised lock) left unscored | Embarrassing miss | Quantisation moved out of the model input (ADR 0001) | **Mitigated** |
| R12 | Grim's open-source aim detection is minimal, so "beating Grim" is a weak claim | Overclaiming value | Add a non-ML statistical baseline in Phase 3 | Open |
| R13 | Children's data: Minecraft has no server-side age signal | Legal (COPPA / GDPR-K / AADC) | Adults-only private allow-listed server; out-of-band verification; gate (policy) | Mitigated by design; awaiting legal review |
| R14 | Behavioural telemetry can identify individuals (mouse-dynamics authentication literature) | Special-category data risk | Treated as special category; ban on using it to identify people; pseudonymisation | Mitigated by design; awaiting legal review |
| R15 | Repo lives in a OneDrive-synced folder | Raw or real data uploaded to a third-party cloud | Raw data only under `$FMAC_DATA_ROOT`; gitignore; collection gate refuses data roots inside sync folders (ADR 0003) | Mitigated |
| R16 | Secrets sit next to the repo (Desktop key files) | Credential leak | Separate repo; defensive `.gitignore`; the owner handles rotation | Owner action |
| R17 | Third-party dataset contains PII (GAN-Aimbots `hwid` = MAC address) | We'd be propagating PII | The ingest code never reads `hwid`; raw files are never committed | Mitigated |
| R18 | Cheat clients are malware-prone | Compromised dev machine | Open-source clients only, in an isolated VM whose only network access is the test server | Planned (Phase 3) |
| R19 | Protocol churn across 1.21.x and future versions | Features break silently | `min_protocol_number` in the spec; per-version Stage A fixtures; CI against new PacketEvents releases | Open (Phase 4) |
| R20 | Automation bias: LLM summaries in the review queue lead reviewers | Unfair flags | Raw evidence shown first; the summary is visually secondary and carries no verdict | Open (Phase 5) |
| R21 | Single modality (rotation only) | Limited coverage | Known limitation | Accepted (future work) |
| R22 | Adults-only training data may cause false positives on unseen populations at deployment | Unfair flags | Shadow-mode false-positive monitoring per population segment before any action path | Open (Phase 4–6) |
