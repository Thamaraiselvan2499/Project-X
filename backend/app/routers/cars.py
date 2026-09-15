from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.models.db_models import Car
from app.models.schemas import CarDetailsRequest, CarOut

router = APIRouter(prefix="/api/cars", tags=["cars"])


@router.put("/{car_number}", response_model=CarOut)
def update_car_details(
    car_number: str, payload: CarDetailsRequest, session: Session = Depends(get_session)
) -> CarOut:
    car = session.get(Car, car_number)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found — log in first to create it")

    car.car_name = payload.car_name
    car.brand = payload.brand
    car.variant = payload.variant
    car.body_type = payload.body_type
    car.damage_type_hint = payload.damage_type_hint
    car.updated_at = datetime.now(timezone.utc)

    session.add(car)
    session.commit()
    session.refresh(car)

    return CarOut(
        car_number=car.car_number,
        owner_mobile_number=car.owner_mobile_number,
        car_name=car.car_name,
        brand=car.brand,
        variant=car.variant,
        body_type=car.body_type,
        damage_type_hint=car.damage_type_hint,
        is_new=False,
    )


@router.get("/{car_number}", response_model=CarOut)
def get_car(car_number: str, session: Session = Depends(get_session)) -> CarOut:
    car = session.get(Car, car_number)
    if car is None:
        raise HTTPException(status_code=404, detail="Car not found")

    return CarOut(
        car_number=car.car_number,
        owner_mobile_number=car.owner_mobile_number,
        car_name=car.car_name,
        brand=car.brand,
        variant=car.variant,
        body_type=car.body_type,
        damage_type_hint=car.damage_type_hint,
        is_new=car.car_name is None,
    )
