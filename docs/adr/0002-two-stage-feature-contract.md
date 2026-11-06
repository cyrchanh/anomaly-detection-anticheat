# ADR 0002 — Two-stage feature contract to control training–serving skew

- **Status:** Accepted (Phase 1)
- **Date:** 2026-10-15

## Context

Training-serving skew is a named first-class risk (brief Part 0.3, original notes §12).
Training runs in Python and inference in Java. If the two compute features even
slightly differently, the model silently scores live data on a distribution it never
saw.

## Decision

Feature computation is split into two stages with a serialisable boundary:

1. **Stage A: packets → `TickRecord` stream.** Java only (Phase 4).
   - Covers PacketEvents capture, tick segmentation on `CLIENT_TICK_END`, detection of
     forced rotations and teleports, and **lag compensation** (reconstructing where
     the client saw each nearby entity).
   - Output format: `schema/tick_record.schema.json`.
   - Stage A will get its own golden fixtures (packet sequences → TickRecords) in Phase 4.
2. **Stage B: `TickRecord`s → `FeatureWindow`s.** Implemented twice, in Python
   (`ml/src/fmac/extractor.py`, the reference) and Java (Phase 4).
   - It is a pure, deterministic function of its input.
   - Every constant is read from `schema/features.yaml` at load time; neither side
     hard-codes thresholds.
   - Both implementations must pass **every** file in `schema/fixtures/` in CI.

Two other rules complete the contract:

- **The training pipeline also consumes `TickRecord`s.** Real shadow-mode data arrives
  as TickRecords captured by the plugin, so training and serving share Stage A *by
  construction*. Python never reimplements Stage A.
- **Model-side transforms are baked into the ONNX graph.** That covers `log1p`/`logit`
  and standardisation (`model_transforms` in the spec), so the Java side feeds raw
  Stage B outputs.

## Numerics

- **All Stage B arithmetic is binary64.** Rotation inputs are binary32, as the client
  sends them.
- **Java uses `StrictMath` (fdlibm) for sin, cos and atan2.** "hypot" means literally
  `sqrt(a*a+b*b)`, because library hypots round differently. The rounding key is
  `floor(x·1e5 + 0.5)`, not banker's rounding.
- **Fixtures are compared with tolerance** (default rel/abs 1e-9), not bit-exactness.
  Thresholds compare a computed value against a constant, so values sitting exactly
  on a threshold could flip between implementations. Fixtures avoid exact boundaries,
  except where the boundary itself is under test, e.g. pitch == 90.0 in A04.

## Fixture kinds

- **`analytic`** fixtures get their expected values from closed-form maths in
  `ml/tools/build_fixtures.py`, **independently** of the extractor. They test that the
  reference implements the spec.
- **`regression`** fixtures are frozen outputs of the Python reference. They can't catch
  a Python bug. They exist to check the Java port on realistic, trig-heavy numerics.
  Regenerating them requires a `spec_version` bump.

## Consequences

- Any spec change means bumping `spec_version` and rebuilding fixtures. Fixtures
  record their `spec_version`, and the test refuses a mismatch.
- The hardest skew risk moves into Stage A, which only Java implements. Its fixtures
  and the plugin's shadow-mode replay tooling are the Phase 4 answer to that.
