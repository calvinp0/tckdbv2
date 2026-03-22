"""Kinetics read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.api.errors import NotFoundError
from app.db.models.kinetics import Kinetics
from app.schemas.entities.kinetics import KineticsRead
from app.api.routes._pagination import PaginatedResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[KineticsRead])
def list_kinetics(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    total = session.scalar(select(func.count(Kinetics.id)))
    rows = session.scalars(
        select(Kinetics)
        .order_by(Kinetics.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[KineticsRead.model_validate(r) for r in rows],
        total=total or 0,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{kinetics_id}", response_model=KineticsRead)
def get_kinetics(kinetics_id: int, session: Session = Depends(get_db)):
    kinetics = session.get(Kinetics, kinetics_id)
    if kinetics is None:
        raise NotFoundError(f"Kinetics {kinetics_id} not found")
    return KineticsRead.model_validate(kinetics)
