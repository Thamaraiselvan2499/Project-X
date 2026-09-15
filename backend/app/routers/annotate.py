from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import AnnotateResponse
from app.services.analysis import analyze_image_bytes
from app.services.quotation import build_quotation

router = APIRouter(prefix="/api", tags=["annotate"])


@router.post("/annotate", response_model=AnnotateResponse)
async def annotate_image(file: UploadFile = File(...)) -> AnnotateResponse:
    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    raw_bytes = await file.read()
    try:
        analysis = analyze_image_bytes(raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    quotation = build_quotation(analysis.detections)

    return AnnotateResponse(
        image_width=analysis.width,
        image_height=analysis.height,
        detections=analysis.detections,
        quotation=quotation,
        model_mode=analysis.model_mode,
    )
