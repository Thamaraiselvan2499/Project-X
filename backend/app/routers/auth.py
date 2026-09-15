from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.models.db_models import Car, User
from app.models.schemas import CarOut, LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    """No OTP: a mobile number / car number pair that hasn't been seen
    before is auto-created rather than rejected. See the caveat on
    LoginRequest in schemas.py."""
    user = session.get(User, payload.mobile_number)
    if user is None:
        user = User(mobile_number=payload.mobile_number)
        session.add(user)

    car = session.get(Car, payload.car_number)
    is_new = car is None
    if car is None:
        car = Car(car_number=payload.car_number, owner_mobile_number=payload.mobile_number)
        session.add(car)

    session.commit()
    session.refresh(car)

    return LoginResponse(
        mobile_number=payload.mobile_number,
        car=CarOut(
            car_number=car.car_number,
            owner_mobile_number=car.owner_mobile_number,
            car_name=car.car_name,
            brand=car.brand,
            variant=car.variant,
            body_type=car.body_type,
            damage_type_hint=car.damage_type_hint,
            is_new=is_new or car.car_name is None,
        ),
    )
