"""Turns detections (damage type + severity) into a repair cost estimate.

Pure functions, no I/O beyond reading the pricing config — kept independent
of FastAPI and the detector so it's trivial to unit test and to reuse from
ml/scripts/evaluate.py for offline sanity checks.
"""
from __future__ import annotations

from app.config import load_pricing
from app.models.schemas import Detection, Quotation, QuotationLineItem


def cost_and_review_for(damage_type: str, severity: str, needs_review: bool) -> tuple[float, bool]:
    """Cost (and whether it should be flagged for manual review) for a
    single (damage_type, severity) pair. Shared by build_quotation, below,
    and the per-part report items endpoint, which stores this same cost
    per detection rather than only as part of an aggregate quotation."""
    damage_costs = load_pricing()["damage_costs"]
    cost_table = damage_costs.get(damage_type)
    if cost_table is None:
        # Unknown class (e.g. taxonomy drift between model and pricing
        # config) — flag for manual review instead of silently costing it
        # at 0 or crashing the request.
        return 0.0, True
    return float(cost_table.get(severity, 0.0)), needs_review


def build_quotation(detections: list[Detection]) -> Quotation:
    pricing = load_pricing()
    service_fee = float(pricing["service_fee"])

    line_items: list[QuotationLineItem] = []
    for det in detections:
        cost, needs_review = cost_and_review_for(det.damage_type, det.severity, det.needs_review)
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
