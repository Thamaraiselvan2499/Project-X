"""SQLModel table definitions.

Kept separate from models/schemas.py (the Pydantic request/response shapes)
so the DB schema and the API contract can evolve independently — a report
response, for instance, nests DamageItem rows under a total that's computed,
not stored as a column.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    # Mobile number is the login identity — no password/OTP for this stage
    # (see CONTRIBUTING.md), so it doubles as the primary key.
    mobile_number: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=_now)


class Car(SQLModel, table=True):
    # Car (registration/license plate) number is the secondary key: it's
    # what a returning customer's session is really keyed on alongside
    # their mobile number, since one person can have more than one car.
    car_number: str = Field(primary_key=True)
    owner_mobile_number: str = Field(foreign_key="user.mobile_number", index=True)

    car_name: str | None = None
    brand: str | None = None
    variant: str | None = None
    body_type: str | None = None  # one of app.config.BODY_TYPES
    damage_type_hint: str | None = None  # customer's own coarse description, not ML output

    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class DamageReport(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    car_number: str = Field(foreign_key="car.car_number", index=True)
    currency: str = "INR"
    created_at: datetime = Field(default_factory=_now)


class DamageItem(SQLModel, table=True):
    """One analyzed photo, tied to the car part the customer pointed out
    on the 3D viewer before uploading it."""

    id: int | None = Field(default=None, primary_key=True)
    report_id: int = Field(foreign_key="damagereport.id", index=True)

    part: str  # one of app.config.part_labels()
    image_path: str  # relative to backend/app/data/uploads/

    damage_type: str | None = None
    severity: str | None = None
    confidence: float | None = None
    area_ratio: float | None = None
    cost: float = 0.0
    needs_review: bool = False
    model_mode: str = "stub"

    created_at: datetime = Field(default_factory=_now)
