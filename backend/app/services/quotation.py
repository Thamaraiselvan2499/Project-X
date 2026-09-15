"""Turns detections (damage type + severity) into a repair cost estimate.

Pure functions, no I/O beyond reading the pricing config — kept independent
of FastAPI and the detector so it's trivial to unit test and to reuse from
ml/scripts/evaluate.py for offline sanity checks.
"""
from __future__ import annotations

from app.config import load_pricing
from app.models.schemas import Detection, Quotation, QuotationLineItem


def build_quotation(detections: list[Detection]) -> Quotation:
    pricing = load_pricing()
    damage_costs = pricing["damage_costs"]
    service_fee = float(pricing["service_fee"])

    line_items: list[QuotationLineItem] = []
    for det in detections:
        cost_table = damage_costs.get(det.damage_type)
        if cost_table is None:
            # Unknown class (e.g. taxonomy drift between model and pricing
            # config) — flag for manual review instead of silently costing
            # it at 0 or crashing the request.
            cost = 0.0
            needs_review = True
        else:
            cost = float(cost_table.get(det.severity, 0.0))
            needs_review = det.needs_review

        line_items.append(
            QuotationLineItem(
                damage_type=det.damage_type,
                severity=det.severity,
                cost=cost,
                needs_review=needs_review,
            )
        )

    subtotal = sum(item.cost for item in line_items)
    total = subtotal + service_fee if line_items else 0.0

    return Quotation(
        currency=pricing["currency"],
        line_items=line_items,
        service_fee=service_fee if line_items else 0.0,
        subtotal=subtotal,
        total=total,
        has_items_needing_review=any(item.needs_review for item in line_items),
    )
