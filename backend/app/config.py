"""Central configuration: file locations and settings loaded from disk/env.

Kept as one small module (no framework-specific settings library) so both
the API and standalone scripts (e.g. ml/scripts/evaluate.py) can import it
without pulling in FastAPI.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

# Trained weights are produced by ml/scripts/train.py and are not committed
# to git (see .gitignore) — override via env var once a model is trained.
MODEL_WEIGHTS_PATH = Path(
    os.environ.get("MODEL_WEIGHTS_PATH", REPO_ROOT / "ml" / "runs" / "train" / "weights" / "best.pt")
)

DAMAGE_CLASSES_PATH = Path(
    os.environ.get("DAMAGE_CLASSES_PATH", REPO_ROOT / "ml" / "configs" / "damage_classes.yaml")
)

PRICING_PATH = Path(
    os.environ.get("PRICING_PATH", APP_DIR / "data" / "pricing.json")
)

# Detections below this confidence are still returned but flagged for
# manual review rather than silently trusted in the quotation.
DETECTION_CONFIDENCE_THRESHOLD = float(os.environ.get("DETECTION_CONFIDENCE_THRESHOLD", "0.25"))

# SQLite file holding users/cars/damage reports. Gitignored like other
# local state — each environment (dev machine, demo, deployment) has its
# own. Override for tests so they don't touch real data.
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", APP_DIR / "data" / "app.db"))

# Where uploaded damage photos are saved (also gitignored).
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", APP_DIR / "data" / "uploads"))

# Body types we have a 3D model shape for in the frontend car viewer.
BODY_TYPES = ["hatchback", "sedan", "suv"]


@lru_cache
def load_damage_taxonomy() -> dict[str, Any]:
    with open(DAMAGE_CLASSES_PATH, "r") as f:
        return yaml.safe_load(f)


@lru_cache
def load_pricing() -> dict[str, Any]:
    with open(PRICING_PATH, "r") as f:
        return json.load(f)


def class_names() -> list[str]:
    return list(load_damage_taxonomy()["classes"])


def severity_thresholds() -> dict[str, float]:
    return dict(load_damage_taxonomy()["severity_thresholds"])


def part_labels() -> list[str]:
    return list(load_damage_taxonomy().get("part_labels", []))
