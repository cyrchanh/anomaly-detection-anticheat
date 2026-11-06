"""Dataset provenance and trust levels (Part 1.5 of the project brief).

Every dataset is registered in a `manifest.yaml` under dataset/<trust-level>/.
Datasets of different trust levels can only be combined through `mix()`, which
requires a stated purpose, checks that purpose's allow-list, and returns a
MixingRecord that downstream artefacts (model cards, eval reports) must carry.
There is deliberately no other way to concatenate across levels.
"""
from __future__ import annotations

import datetime as _dt
import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from fmac.spec import SCHEMA_DIR

DATASET_ROOT = SCHEMA_DIR.parent / "dataset"


class TrustLevel(str, enum.Enum):
    REAL_CONSENTED = "real-consented"
    PUBLIC_REFERENCE = "public-reference"
    SYNTHETIC_CALIBRATED = "synthetic-calibrated"
    SYNTHETIC_ADVERSARIAL = "synthetic-adversarial"


class Purpose(str, enum.Enum):
    TRAIN_NORMAL = "train-normal"          # data the flow learns as "legitimate"
    CALIBRATE = "calibrate"                # fitting synthetic-generator parameters
    EVAL_LEGIT = "eval-legit"              # false-positive measurement
    EVAL_CHEAT = "eval-cheat"              # detection measurement
    STRESS_TEST = "stress-test"


# Which trust levels may feed which purpose. Note what is ABSENT:
# * adversarial data never trains "normal";
# * synthetic data is never the basis of a false-positive claim about real players.
ALLOWED: dict[Purpose, frozenset[TrustLevel]] = {
    Purpose.TRAIN_NORMAL: frozenset({TrustLevel.REAL_CONSENTED, TrustLevel.SYNTHETIC_CALIBRATED}),
    Purpose.CALIBRATE: frozenset({TrustLevel.REAL_CONSENTED, TrustLevel.PUBLIC_REFERENCE}),
    Purpose.EVAL_LEGIT: frozenset({TrustLevel.REAL_CONSENTED}),
    Purpose.EVAL_CHEAT: frozenset({TrustLevel.REAL_CONSENTED, TrustLevel.PUBLIC_REFERENCE, TrustLevel.SYNTHETIC_ADVERSARIAL}),
    Purpose.STRESS_TEST: frozenset(TrustLevel),
}


class ProvenanceError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatasetRef:
    id: str
    trust_level: TrustLevel
    license: str
    usable: bool
    entry: dict[str, Any]

    def __add__(self, other: object):  # make accidental concatenation loud
        raise ProvenanceError("DatasetRefs cannot be added; use fmac.provenance.mix() with an explicit purpose")


@dataclass(frozen=True)
class MixingRecord:
    purpose: Purpose
    datasets: tuple[str, ...]
    trust_levels: tuple[str, ...]
    reason: str
    created_utc: str
    weights: dict[str, float] = field(default_factory=dict)


def _manifest_schema() -> dict[str, Any]:
    with open(SCHEMA_DIR / "dataset_manifest.schema.json", encoding="utf-8") as f:
        import json
        return json.load(f)


def load_manifests(root: Path = DATASET_ROOT) -> dict[str, DatasetRef]:
    schema = _manifest_schema()
    refs: dict[str, DatasetRef] = {}
    for level in TrustLevel:
        path = root / level.value / "manifest.yaml"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {"datasets": []}
        jsonschema.validate(doc, schema)
        for entry in doc["datasets"]:
            if entry["trust_level"] != level.value:
                raise ProvenanceError(f"{entry['id']} declares {entry['trust_level']} but lives under {level.value}/")
            if entry["id"] in refs:
                raise ProvenanceError(f"duplicate dataset id {entry['id']}")
            refs[entry["id"]] = DatasetRef(entry["id"], level, entry["license"]["spdx"], entry["usable"], entry)
    return refs


def mix(datasets: list[DatasetRef], *, purpose: Purpose, reason: str,
        weights: dict[str, float] | None = None) -> MixingRecord:
    if not reason.strip():
        raise ProvenanceError("a mixing step needs a written reason")
    for d in datasets:
        if not d.usable:
            raise ProvenanceError(f"{d.id} is marked usable=false ({d.entry.get('usability_notes', 'see manifest')})")
        if d.trust_level not in ALLOWED[purpose]:
            raise ProvenanceError(f"{d.id} ({d.trust_level.value}) is not allowed for purpose {purpose.value}")
        if d.trust_level is TrustLevel.REAL_CONSENTED and not d.entry.get("consent_gate", {}).get("signed_off"):
            raise ProvenanceError(f"{d.id}: real-player data without consent-gate sign-off (docs/privacy-consent-policy-DRAFT.md)")
    return MixingRecord(
        purpose=purpose,
        datasets=tuple(d.id for d in datasets),
        trust_levels=tuple(d.trust_level.value for d in datasets),
        reason=reason,
        created_utc=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        weights=dict(weights or {}),
    )
