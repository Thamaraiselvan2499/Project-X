"""Shared "bytes in, detections out" pipeline used by both the standalone
/api/annotate endpoint and the per-part report item endpoint, so the two
don't drift into slightly different behavior."""
from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image

from app.config import load_pricing
from app.models.schemas import BoundingBox, Detection
from app.services.detector import detect
from app.services.severity import estimate_severity


@dataclass
class ImageAnalysis:
    width: int
    height: int
    detections: list[Detection]
    model_mode: str


def analyze_image_bytes(raw_bytes: bytes) -> ImageAnalysis:
    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except Exception as exc:  # Pillow raises various subclasses of Exception here
        raise ValueError(f"Could not read image: {exc}") from exc

    width, height = image.size
    image_area = float(width * height)
    low_conf_threshold = load_pricing()["low_confidence_threshold"]

    result = detect(image)

    detections: list[Detection] = []
    for raw in result.detections:
        box_area = max(0.0, raw.x_max - raw.x_min) * max(0.0, raw.y_max - raw.y_min)
        area_ratio = box_area / image_area if image_area else 0.0
        detections.append(
            Detection(
                damage_type=raw.damage_type,
                confidence=raw.confidence,
                bbox=BoundingBox(x_min=raw.x_min, y_min=raw.y_min, x_max=raw.x_max, y_max=raw.y_max),
                area_ratio=area_ratio,
                severity=estimate_severity(area_ratio),
                needs_review=raw.confidence < low_conf_threshold,
            )
        )

    return ImageAnalysis(width=width, height=height, detections=detections, model_mode=result.mode)
