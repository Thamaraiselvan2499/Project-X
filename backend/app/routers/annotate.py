from __future__ import annotations

import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image

from app.config import load_pricing
from app.models.schemas import AnnotateResponse, BoundingBox, Detection
from app.services.detector import detect
from app.services.quotation import build_quotation
from app.services.severity import estimate_severity

router = APIRouter(prefix="/api", tags=["annotate"])


@router.post("/annotate", response_model=AnnotateResponse)
async def annotate_image(file: UploadFile = File(...)) -> AnnotateResponse:
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    raw_bytes = await file.read()
    try:
        image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except Exception as exc:  # Pillow raises various subclasses of Exception here
        raise HTTPException(status_code=400, detail=f"Could not read image: {exc}") from exc

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

    quotation = build_quotation(detections)

    return AnnotateResponse(
        image_width=width,
        image_height=height,
        detections=detections,
        quotation=quotation,
        model_mode=result.mode,
    )
