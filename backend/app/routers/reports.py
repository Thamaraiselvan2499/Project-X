from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select

from app.config import load_pricing, part_labels
from app.db import get_session
from app.models.db_models import Car, DamageItem, DamageReport
from app.models.schemas import (
    AddItemResponse,
    DamageItemOut,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportOut,
)
from app.services.analysis import analyze_image_bytes
from app.services.quotation import cost_and_review_for
from app.services.storage import save_upload

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _to_report_out(report: DamageReport, items: list[DamageItem]) -> ReportOut:
    service_fee = float(load_pricing()["service_fee"])
    subtotal = sum(item.cost for item in items)
    return ReportOut(
        id=report.id,
        car_number=report.car_number,
        currency=report.currency,
        items=[
            DamageItemOut(
                id=item.id,
                part=item.part,
                damage_type=item.damage_type,
                severity=item.severity,
                confidence=item.confidence,
                area_ratio=item.area_ratio,
                cost=item.cost,
                needs_review=item.needs_review,
                model_mode=item.model_mode,
            )
            for item in items
        ],
        subtotal=subtotal,
        service_fee=service_fee if items else 0.0,
        total=subtotal + service_fee if items else 0.0,
        has_items_needing_review=any(item.needs_review for item in items),
    )


@router.post("", response_model=ReportCreateResponse)
def create_report(payload: ReportCreateRequest, session: Session = Depends(get_session)) -> ReportCreateResponse:
    car = session.get(Car, payload.car_number)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found — log in first to create it")

    report = DamageReport(car_number=car.car_number, currency=load_pricing()["currency"])
    session.add(report)
    session.commit()
    session.refresh(report)

    return ReportCreateResponse(report_id=report.id, car_number=report.car_number, currency=report.currency)


@router.post("/{report_id}/items", response_model=AddItemResponse)
async def add_report_item(
    report_id: int,
    part: str = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> AddItemResponse:
    report = session.get(DamageReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if part not in part_labels():
        raise HTTPException(status_code=400, detail=f"Unknown part '{part}'")

    if file.content_type is None or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")

    raw_bytes = await file.read()
    try:
        analysis = analyze_image_bytes(raw_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    image_path = save_upload(report_id, part, file.filename, raw_bytes)

    new_items: list[DamageItem] = []
    if analysis.detections:
        for det in analysis.detections:
            cost, needs_review = cost_and_review_for(det.damage_type, det.severity, det.needs_review)
            new_items.append(
                DamageItem(
                    report_id=report_id,
                    part=part,
                    image_path=str(image_path),
                    damage_type=det.damage_type,
                    severity=det.severity,
                    confidence=det.confidence,
                    area_ratio=det.area_ratio,
                    cost=cost,
                    needs_review=needs_review,
                    model_mode=analysis.model_mode,
                )
            )
    else:
        # No damage found in this photo — still record it (image_path,
        # model_mode) so the report shows every part the customer checked,
        # not just the ones with a positive detection.
        new_items.append(
            DamageItem(
                report_id=report_id,
                part=part,
                image_path=str(image_path),
                model_mode=analysis.model_mode,
            )
        )

    for item in new_items:
        session.add(item)
    session.commit()
    for item in new_items:
        session.refresh(item)

    all_items = session.exec(select(DamageItem).where(DamageItem.report_id == report_id)).all()

    return AddItemResponse(
        added_items=[
            DamageItemOut(
                id=item.id,
                part=item.part,
                damage_type=item.damage_type,
                severity=item.severity,
                confidence=item.confidence,
                area_ratio=item.area_ratio,
                cost=item.cost,
                needs_review=item.needs_review,
                model_mode=item.model_mode,
            )
            for item in new_items
        ],
        report=_to_report_out(report, list(all_items)),
    )


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, session: Session = Depends(get_session)) -> ReportOut:
    report = session.get(DamageReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    items = session.exec(select(DamageItem).where(DamageItem.report_id == report_id)).all()
    return _to_report_out(report, list(items))
