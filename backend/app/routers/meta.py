from __future__ import annotations

from fastapi import APIRouter

from app.config import BODY_TYPES, class_names, part_labels
from app.models.schemas import TaxonomyResponse

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/taxonomy", response_model=TaxonomyResponse)
def get_taxonomy() -> TaxonomyResponse:
    """Single source of truth (ml/configs/damage_classes.yaml) served to the
    frontend, so the car-details form's body-type options and the 3D
    viewer's clickable part list can't drift out of sync with the backend."""
    return TaxonomyResponse(
        damage_classes=class_names(),
        part_labels=part_labels(),
        body_types=BODY_TYPES,
    )
