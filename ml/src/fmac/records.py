"""TickRecord parsing (Stage B input). See schema/tick_record.schema.json."""
from __future__ import annotations

import functools
import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from fmac.spec import SCHEMA_DIR

_NONFINITE = {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}


def to_f32(x: float) -> float:
    """Round a Python float to the nearest binary32, returned as binary64."""
    if not math.isfinite(x):
        return x
    return struct.unpack("<f", struct.pack("<f", x))[0]


def decode_float(v: Any) -> float:
    if isinstance(v, str):
        return _NONFINITE[v]
    return float(v)


def encode_float(x: float) -> float | str:
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    return x


@dataclass(frozen=True)
class EntityView:
    rel: tuple[float, float, float]
    half_width: float
    is_player: bool


@dataclass(frozen=True)
class TickRecord:
    tick: int
    yaw: float      # a binary32 value held in a binary64
    pitch: float
    rot_sent: bool
    forced_rotation: bool
    attack_target: int | None
    held_item: str
    self_pos: tuple[float, float, float]
    ping_ms: float
    entities: dict[int, EntityView]


@functools.cache
def _validator() -> jsonschema.Draft202012Validator:
    with open(SCHEMA_DIR / "tick_record.schema.json", encoding="utf-8") as f:
        return jsonschema.Draft202012Validator(json.load(f))


def parse_session(doc: dict[str, Any]) -> list[TickRecord]:
    """Validate a session document against the JSON Schema and parse it."""
    _validator().validate(doc)
    out = []
    for t in doc["ticks"]:
        out.append(TickRecord(
            tick=t["tick"],
            yaw=to_f32(decode_float(t["yaw"])),
            pitch=to_f32(decode_float(t["pitch"])),
            rot_sent=t["rot_sent"],
            forced_rotation=t["forced_rotation"],
            attack_target=t["attack_target"],
            held_item=t["held_item"],
            self_pos=tuple(float(c) for c in t["self_pos"]),
            ping_ms=float(t["ping_ms"]),
            entities={
                int(k): EntityView(tuple(float(c) for c in e["rel"]), float(e["half_width"]), e["is_player"])
                for k, e in t["entities"].items()
            },
        ))
    return out


def load_session(path: Path) -> list[TickRecord]:
    with open(path, encoding="utf-8") as f:
        return parse_session(json.load(f))
