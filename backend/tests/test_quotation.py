from app.models.schemas import BoundingBox, Detection
from app.services.quotation import build_quotation
from app.services.severity import estimate_severity


def make_detection(damage_type: str, severity: str, confidence: float = 0.9) -> Detection:
    return Detection(
        damage_type=damage_type,
        confidence=confidence,
        bbox=BoundingBox(x_min=0, y_min=0, x_max=10, y_max=10),
        area_ratio=0.01,
        severity=severity,
        needs_review=confidence < 0.5,
    )


def test_empty_detections_gives_zero_quotation():
    quotation = build_quotation([])
    assert quotation.total == 0.0
    assert quotation.subtotal == 0.0
    assert quotation.line_items == []


def test_single_detection_adds_service_fee():
    quotation = build_quotation([make_detection("scratch", "minor")])
    assert len(quotation.line_items) == 1
    assert quotation.line_items[0].cost == 800
    assert quotation.subtotal == 800
    assert quotation.total == 800 + quotation.service_fee


def test_multiple_detections_sum_costs_plus_single_service_fee():
    detections = [make_detection("scratch", "minor"), make_detection("dent", "severe")]
    quotation = build_quotation(detections)
    assert quotation.subtotal == 800 + 8000
    assert quotation.total == quotation.subtotal + quotation.service_fee


def test_unknown_damage_type_is_flagged_for_review_not_crashed():
    quotation = build_quotation([make_detection("unknown_class", "minor")])
    assert quotation.line_items[0].cost == 0.0
    assert quotation.line_items[0].needs_review is True
    assert quotation.has_items_needing_review is True


def test_low_confidence_detection_flagged_but_still_costed():
    quotation = build_quotation([make_detection("dent", "moderate", confidence=0.3)])
    assert quotation.has_items_needing_review is True
    assert quotation.line_items[0].cost == 3500


def test_severity_thresholds_are_monotonic():
    assert estimate_severity(0.0) == "minor"
    assert estimate_severity(0.019) == "minor"
    assert estimate_severity(0.02) == "moderate"
    assert estimate_severity(0.079) == "moderate"
    assert estimate_severity(0.08) == "severe"
    assert estimate_severity(0.5) == "severe"
