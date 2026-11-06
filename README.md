# FMAC — Flow-Matching Anticheat (Minecraft Java 1.21.2+, Paper)

A server-side anomaly-detection anticheat for PvP aim. It learns what legitimate aim
looks like and flags deviations, combined with protocol-level hard rules.
**Status: Phase 1 of 6. No plugin yet, no model yet, no collection from real players.**

| Path | What |
|---|---|
| `schema/` | **Single source of truth**: `features.yaml`, JSON Schemas, golden fixtures |
| `ml/` | Python reference extractor (`fmac`), provenance system, fixture builder, calibration scripts. Training arrives in Phase 2. |
| `dataset/` | Manifests only, by trust level. Raw data lives under `$FMAC_DATA_ROOT`, **never in this repo** |
| `docs/` | Brief, ADRs, risk register, tradeoff log, literature survey, calibration report, **privacy policy DRAFT** |
| `plugin/`, `eval/`, `review-ui/` | Later phases (see their READMEs) |

## Quick start
```
pip install -e "ml[dev]"
python -m pytest ml            # spec, fixtures, sensitivity, provenance
python ml/tools/build_fixtures.py   # only after a spec_version bump
```

## Safety gates (non-negotiable)
- Nothing issues a ban. The Yellow-Flag path (Phase 6) needs explicit owner approval.
- Real-player collection is off until the conditions in `docs/privacy-consent-policy-DRAFT.md` §14 are met (ADR 0003).
- No LLM in the real-time scoring or decision path.
- Clients never receive scores, flags or any other suspicion signal.
