# Conservative-tradeoff log

Standing instruction: whenever detection is traded against false positives on real
players, **default to missing cheaters over flagging legitimate players**, and record
it here. Each entry names the cost being accepted.

| ID | Where | Choice | Cost accepted (cheats we may miss) | Revisit when |
|---|---|---|---|---|
| CT-01 | `features.yaml` sensitivity estimator / quantisation channel | With no sensitivity estimate (e.g. zoom mods, cinematic camera, hand-edited sensitivity, or an un-quantised cheat), `quant_residual_yaw` is null. A missing estimate is **context shown to reviewers, never evidence**. | A cheat that never quantises gets no penalty *from this channel*. The flow model still scores it on the other 11 features: R02 has lag-0 correlation 0.999 and aim error ≈ 0.01. | Phase 3, once we know how often legitimate players lack an estimate |
| CT-02 | `HR_CENTER_LOCK` | Shipped **disabled**. Becomes evidence only after Phase 3 measures its false-positive rate on consented legitimate play and real lag-compensation error. | Blatant lock-on aimbots aren't caught by this rule until then. | Phase 3 |
| CT-03 | Window validity | Any forced rotation, tick gap, non-finite rotation, target lost from tracking, or target outside 0.5–6 blocks → window **invalid, never scored, never evidence**. | A cheater who triggers teleports or desync, or fights near the edge of range, produces fewer scored windows. Invalid-window *rates* are surfaced to reviewers. | Phase 4, using real invalid-rate data |
| CT-04 | Rule semantics | Hard-rule hits feed the Yellow-Flag accumulator; **no rule causes automated action**. Even `HR_PITCH_RANGE`, which a vanilla client can't trigger, only produces a review item. | Slower response to provably modified clients. Grim and Paper kick for many invalid packets anyway. | Phase 6+, only with your explicit approval |
| CT-05 | Decision tiers (design, built in Phase 6) | Percentile tiers from the original notes are rejected. Under "ban at ≥p99", **1% of legitimate encounters would be banned by construction**. Tiers will instead come from an explicit false-positive budget per player per time window, enforced by a sequential test across windows. | Detection is slower, because several suspicious windows are needed before any Yellow Flag. | Phase 6 design review |
| CT-06 | Age and data scope | Collection is adults-only on an allow-listed private server (policy §2–3). | A smaller, less diverse dataset, which raises the risk of false positives on populations we never saw (younger or less skilled players) once deployed. This needs a deployment-side mitigation later. | Legal review |
