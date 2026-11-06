# Project brief — decisions of record

Source: the project owner's spec (2026-10-15), which builds on the hackathon document
*"Flow Matching for Minecraft PvP Anticheat — Consolidated Notes (Full Draft)"*.
That document is treated as a **design spec, not working code**. No prototype code
exists, so everything is rebuilt from scratch.

## Fixed decisions (Part 0) — revisit only with strong justification

1. **Server-side Paper plugin.** A client mod is allowed only as optional, opt-in
   telemetry on a consenting test server.
2. **Stack:**
   - Paper (not Folia by default)
   - PacketEvents
   - ONNX via DJL + ONNX Runtime, run **off the main thread**
   - PyTorch for offline training
   - No Kafka or Spark for a single server
3. **One shared feature schema** with golden fixtures that run in CI on both the Python
   and Java sides (ADR 0002).
4. **Safety-first rollout:**
   shadow mode → compare against baseline → Yellow Flag only, with human review → much
   later, if ever, automated action (and only with an appeals process).
   **An unvalidated model never issues a real ban.** This overrides later requests
   unless the owner says *"I understand this bypasses the safety gate."*
5. **Features redesigned around what the protocol actually exposes** (ADR 0001).
6. **No LLM or agent in the real-time scoring or decision path.** Offline uses only.

## Answers to the Phase 0 questions (2026-10-15)

| Topic | Decision |
|---|---|
| Repo | Separate git repo in this folder; never references the parent Desktop. Defensive `.gitignore`. The owner handles the Desktop key files. |
| Prototype code | None. Rebuild from the spec; document every departure. |
| Jurisdiction | Undecided. Draft against the strictest combination of COPPA, GDPR/GDPR-K and the UK AADC. Mark as DRAFT. **Collection stays gated** until legal review **and** written sign-off. |
| Age | Never under 13. Under 16 excluded by default; parental consent only as a documented future option. Server-level gating, never client-reported. **Open:** the policy draft proposes **18+**, because the AADC covers under-18s. Needs an owner decision on legal advice. |
| Version | **1.21.x only, post-1.9 combat.** No 1.8 or ViaVersion legacy combat. *Implementation note:* the floor is **1.21.2**, which added `CLIENT_TICK_END`. |
| Visibility | Repo and weights private. GPL-3.0 still tracked (ADR 0004). |
| Cheat clients | Open source only (Wurst, Meteor, LiquidBounce), in an isolated VM. Gaps are filled by the synthetic hard-negative generator. |
| Standing instruction | Default to conservative on accuracy-vs-false-positive tradeoffs, and log each one (`docs/conservative-tradeoffs.md`). |

## Phases

| Phase | Scope | Status |
|---|---|---|
| 1 | Schema, feature redesign, reference extractor, fixtures, provenance, dataset survey, privacy DRAFT | **Done, awaiting review** |
| 2 | Synthetic v2 + hard negatives, conditional flow matching, baselines, ONNX export, load benchmark | Not started |
| 3 | Grim + statistical baseline comparison on shared traffic | Not started |
| 4 | Paper plugin, shadow mode only (Stage A, Java Stage B, async inference, SQLite) | Not started |
| 5 | Review UI | Not started |
| 6 | Yellow-Flag action path | **Requires explicit owner approval** |
