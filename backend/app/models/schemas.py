"""Pydantic request/response models shared by the routers and services."""
from __future__ import annotations

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class Detection(BaseModel):
    damage_type: str
    confidence: float
    bbox: BoundingBox
    area_ratio: float = Field(..., description="Detection area / image area, 0-1")
    severity: str
    needs_review: bool = Field(
        False, description="True when confidence is below the low-confidence threshold"
    )


class QuotationLineItem(BaseModel):
    damage_type: str
    severity: str
    cost: float
    needs_review: bool


class Quotation(BaseModel):
    currency: str
    line_items: list[QuotationLineItem]
    service_fee: float
    subtotal: float
    total: float
    has_items_needing_review: bool


class AnnotateResponse(BaseModel):
    image_width: int
    image_height: int
    detections: list[Detection]
    quotation: Quotation
    model_mode: str = Field(
        ..., description="'trained' when real model weights were used, 'stub' for demo/placeholder output"
    )
