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


# --- Auth / car / report flow -----------------------------------------
#
# No OTP at this stage (see CONTRIBUTING.md) — logging in with a mobile
# number that hasn't been seen before auto-creates the account, same for
# the car number. This is deliberately not secure (anyone who knows a
# customer's mobile + car number can open their account); it's scoped for
# an internal pilot, not a production launch.


class LoginRequest(BaseModel):
    mobile_number: str = Field(..., min_length=6, max_length=15)
    car_number: str = Field(..., min_length=3, max_length=20)


class CarOut(BaseModel):
    car_number: str
    owner_mobile_number: str
    car_name: str | None
    brand: str | None
    variant: str | None
    body_type: str | None
    damage_type_hint: str | None
    is_new: bool = Field(..., description="True if this car had no saved details yet (skip straight to car details form)")


class LoginResponse(BaseModel):
    mobile_number: str
    car: CarOut


class CarDetailsRequest(BaseModel):
    car_name: str
    brand: str
    variant: str
    body_type: str
    damage_type_hint: str | None = None


class ReportCreateRequest(BaseModel):
    car_number: str


class ReportCreateResponse(BaseModel):
    report_id: int
    car_number: str
    currency: str


class DamageItemOut(BaseModel):
    id: int
    part: str
    damage_type: str | None
    severity: str | None
    confidence: float | None
    area_ratio: float | None
    cost: float
    needs_review: bool
    model_mode: str


class ReportOut(BaseModel):
    id: int
    car_number: str
    currency: str
    items: list[DamageItemOut]
    subtotal: float
    service_fee: float
    total: float
    has_items_needing_review: bool


class TaxonomyResponse(BaseModel):
    damage_classes: list[str]
    part_labels: list[str]
    body_types: list[str]


class AddItemResponse(BaseModel):
    added_items: list[DamageItemOut] = Field(..., description="Rows created from this one upload")
    report: ReportOut = Field(..., description="Full report, recomputed with this upload included")
