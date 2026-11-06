"""Minecraft rotation geometry (features.yaml#tick_record.minecraft_axes, #aim_error)."""
from __future__ import annotations

import math
import struct


def hyp(a: float, b: float) -> float:
    """sqrt(a*a + b*b) computed literally (NOT math.hypot) for Java parity."""
    return math.sqrt(a * a + b * b)


def wrap180(x: float) -> float:
    return x - 360.0 * math.floor((x + 180.0) / 360.0)


def look(yaw_deg: float, pitch_deg: float) -> tuple[float, float, float]:
    y = math.radians(yaw_deg)
    p = math.radians(pitch_deg)
    cp = math.cos(p)
    return (-math.sin(y) * cp, -math.sin(p), math.cos(y) * cp)


def bearing(rel: tuple[float, float, float]) -> tuple[float, float]:
    dx, dy, dz = rel
    return (math.degrees(math.atan2(-dx, dz)), math.degrees(-math.atan2(dy, hyp(dx, dz))))


def norm3(v: tuple[float, float, float]) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def normalised_aim_error(yaw: float, pitch: float, rel: tuple[float, float, float], half_width: float) -> float:
    v = look(yaw, pitch)
    n = norm3(rel)
    u = (rel[0] / n, rel[1] / n, rel[2] / n)
    cx = v[1] * u[2] - v[2] * u[1]
    cy = v[2] * u[0] - v[0] * u[2]
    cz = v[0] * u[1] - v[1] * u[0]
    err = math.degrees(math.atan2(math.sqrt(cx * cx + cy * cy + cz * cz), v[0] * u[0] + v[1] * u[1] + v[2] * u[2]))
    r = math.degrees(math.atan2(half_width, max(hyp(rel[0], rel[2]), 0.1)))
    return err / r


def ulp32(x: float) -> float:
    """Spacing between |x| (as binary32) and the next larger binary32."""
    ax = abs(x)
    bits = struct.unpack("<I", struct.pack("<f", ax))[0]
    nxt = struct.unpack("<f", struct.pack("<I", bits + 1))[0]
    return nxt - struct.unpack("<f", struct.pack("<f", ax))[0]
