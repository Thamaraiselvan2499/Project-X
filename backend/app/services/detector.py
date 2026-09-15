"""Damage detector wrapper.

Loads a trained YOLO model (produced by ml/scripts/train.py) when weights
are present at app.config.MODEL_WEIGHTS_PATH. Until the team has trained
and dropped in weights, `detect` runs in "stub" mode: it returns a small
set of deterministic, clearly-labeled placeholder detections so the rest
of the pipeline (severity -> quotation -> API -> frontend) can be built
and tested end-to-end without blocking on training.

Nothing about the public `detect()` signature changes between stub and
trained mode — callers don't need to know which one is active, they just
read `result.mode`.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PIL import Image

from app.config import DETECTION_CONFIDENCE_THRESHOLD, MODEL_WEIGHTS_PATH, class_names


@dataclass
class RawDetection:
    damage_type: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass
class DetectionResult:
    detections: list[RawDetection]
    mode: str  # "trained" or "stub"


@lru_cache
def _load_model():
    if not MODEL_WEIGHTS_PATH.exists():
        return None
    try:
        from ultralytics import YOLO
    except ImportError:
        return None
    return YOLO(str(MODEL_WEIGHTS_PATH))


def _stub_detect(width: int, height: int) -> list[RawDetection]:
    """Deterministic placeholder output for local/demo use before a model
    is trained. Roughly places one small and one larger box so both minor
    and severe severity paths are exercised."""
    names = class_names()
    return [
        RawDetection(
            damage_type=names[0] if names else "scratch",
            confidence=0.81,
            x_min=width * 0.10,
            y_min=height * 0.15,
            x_max=width * 0.20,
            y_max=height * 0.20,
        ),
        RawDetection(
            damage_type=names[1] if len(names) > 1 else "dent",
            confidence=0.68,
            x_min=width * 0.45,
            y_min=height * 0.40,
            x_max=width * 0.75,
            y_max=height * 0.70,
        ),
    ]


def detect(image: Image.Image) -> DetectionResult:
    width, height = image.size
    model = _load_model()

    if model is None:
        return DetectionResult(detections=_stub_detect(width, height), mode="stub")

    names = class_names()
    raw: list[RawDetection] = []
    results = model.predict(image, conf=DETECTION_CONFIDENCE_THRESHOLD, verbose=False)
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        for box, conf, cls_idx in zip(boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist()):
            x_min, y_min, x_max, y_max = box
            class_name = names[int(cls_idx)] if int(cls_idx) < len(names) else str(int(cls_idx))
            raw.append(
                RawDetection(
                    damage_type=class_name,
                    confidence=float(conf),
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max,
                )
            )
    return DetectionResult(detections=raw, mode="trained")
