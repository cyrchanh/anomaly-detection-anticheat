# schema/

- `features.yaml`: normative Stage B spec (constants, formulas, rules, validity). Both extractors load it.
- `tick_record.schema.json`: Stage A → Stage B interchange format.
- `dataset_manifest.schema.json`: format of `dataset/*/manifest.yaml`.
- `fixtures/`: golden fixtures. `A*` = **analytic** (expected values derived independently); `R*` = **regression** (frozen Python output, for Java parity).

Changing anything that affects outputs requires: bump `spec_version` → `python ml/tools/build_fixtures.py` → review the fixture diff → update ADR 0001 if features changed.
