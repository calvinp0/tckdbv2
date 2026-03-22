"""Thermo read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.api.errors import NotFoundError
from app.db.models.thermo import Thermo
from app.schemas.entities.thermo import ThermoRead
from app.api.routes._pagination import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ThermoRead])
def list_thermo(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    total = session.scalar(select(func.count(Thermo.id)))
    rows = session.scalars(
        select(Thermo)
        .order_by(Thermo.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[ThermoRead.model_validate(r) for r in rows],
        total=total or 0,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{thermo_id}", response_model=ThermoRead)
def get_thermo(thermo_id: int, session: Session = Depends(get_db)):
    thermo = session.get(Thermo, thermo_id)
    if thermo is None:
        raise NotFoundError(f"Thermo {thermo_id} not found")
    return ThermoRead.model_validate(thermo)
