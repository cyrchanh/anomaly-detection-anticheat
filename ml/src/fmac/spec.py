"""Loads schema/features.yaml — the single source of truth for every constant.

Nothing in the extractor hard-codes a threshold; it reads it from here, so the
Java side (which reads the same file) cannot silently drift on constants.
"""
from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml

# ml/src/fmac/spec.py -> repo root is three parents up from this package dir.
# Resolution never walks above the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = Path(os.environ.get("FMAC_SCHEMA_DIR", _REPO_ROOT / "schema"))


@functools.cache
def load_spec() -> dict[str, Any]:
    with open(SCHEMA_DIR / "features.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def feature_names() -> list[str]:
    return [f["name"] for f in load_spec()["features"]]


def context_names() -> list[str]:
    return [c["name"] for c in load_spec()["context"]]


def rule_specs() -> list[dict[str, Any]]:
    return load_spec()["rules"]
