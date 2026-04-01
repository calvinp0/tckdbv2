"""Conformer group and observation read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.api.errors import NotFoundError
from app.api.routes._pagination import PaginatedResponse
from app.db.models.common import ScientificOriginKind
from app.db.models.species import ConformerGroup, ConformerObservation
from app.schemas.entities.conformer import ConformerGroupRead, ConformerObservationRead

groups_router = APIRouter()
observations_router = APIRouter()


# ---------------------------------------------------------------------------
# Conformer groups
# ---------------------------------------------------------------------------


@groups_router.get("", response_model=PaginatedResponse[ConformerGroupRead])
def list_conformer_groups(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    species_entry_id: int | None = Query(None),
    label: str | None = Query(None),
):
    base = select(ConformerGroup.id)
    if species_entry_id is not None:
        base = base.where(ConformerGroup.species_entry_id == species_entry_id)
    if label is not None:
        base = base.where(ConformerGroup.label == label)

    total = session.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    rows = session.scalars(
        select(ConformerGroup)
        .where(ConformerGroup.id.in_(base))
        .order_by(ConformerGroup.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[ConformerGroupRead.model_validate(r) for r in rows],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@groups_router.get("/{group_id}", response_model=ConformerGroupRead)
def get_conformer_group(group_id: int, session: Session = Depends(get_db)):
    row = session.get(ConformerGroup, group_id)
    if row is None:
        raise NotFoundError(f"ConformerGroup {group_id} not found")
    return ConformerGroupRead.model_validate(row)


# ---------------------------------------------------------------------------
# Conformer observations (mounted under /conformer-observations in router.py)
# ---------------------------------------------------------------------------


@observations_router.get(
    "", response_model=PaginatedResponse[ConformerObservationRead]
)
def list_conformer_observations(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    conformer_group_id: int | None = Query(None),
    assignment_scheme_id: int | None = Query(None),
    scientific_origin: ScientificOriginKind | None = Query(None),
):
    base = select(ConformerObservation.id)
    if conformer_group_id is not None:
        base = base.where(
            ConformerObservation.conformer_group_id == conformer_group_id
        )
    if assignment_scheme_id is not None:
        base = base.where(
            ConformerObservation.assignment_scheme_id == assignment_scheme_id
        )
    if scientific_origin is not None:
        base = base.where(
            ConformerObservation.scientific_origin == scientific_origin
        )

    total = session.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    rows = session.scalars(
        select(ConformerObservation)
        .where(ConformerObservation.id.in_(base))
        .order_by(ConformerObservation.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[ConformerObservationRead.model_validate(r) for r in rows],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@observations_router.get(
    "/{observation_id}", response_model=ConformerObservationRead
)
def get_conformer_observation(
    observation_id: int, session: Session = Depends(get_db)
):
    row = session.get(ConformerObservation, observation_id)
    if row is None:
        raise NotFoundError(f"ConformerObservation {observation_id} not found")
    return ConformerObservationRead.model_validate(row)
