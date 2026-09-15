"""Maps a detection's area ratio to a severity bucket.

This is a deliberately simple heuristic for the MVP: severity scales with
how much of the frame the damage covers. It's a placeholder for a learned
severity model — swap `estimate_severity` out once we have severity labels
to train on, without touching callers (they only depend on this function's
signature).
"""
from __future__ import annotations

from app.config import severity_thresholds

SEVERITY_ORDER = ["minor", "moderate", "severe"]


def estimate_severity(area_ratio: float) -> str:
    thresholds = severity_thresholds()
    if area_ratio < thresholds["minor"]:
        return "minor"
    if area_ratio < thresholds["moderate"]:
        return "moderate"
    return "severe"
