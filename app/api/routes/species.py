"""Species and species-entry read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import PaginationParams, get_db
from app.api.errors import NotFoundError
from app.db.models.common import MoleculeKind
from app.db.models.species import (
    ConformerGroup,
    ConformerObservation,
    Species,
    SpeciesEntry,
)
from app.db.models.statmech import Statmech
from app.db.models.thermo import Thermo
from app.db.models.transport import Transport
from app.schemas.entities.conformer import ConformerObservationRead
from app.schemas.entities.species import SpeciesRead
from app.schemas.entities.species_entry import SpeciesEntryRead
from app.schemas.entities.statmech import StatmechRead
from app.schemas.entities.thermo import ThermoRead
from app.schemas.entities.transport import TransportRead
from app.api.routes._pagination import PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[SpeciesRead])
def list_species(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
    smiles: str | None = Query(None),
    inchi_key: str | None = Query(None),
    charge: int | None = Query(None),
    multiplicity: int | None = Query(None),
    kind: MoleculeKind | None = Query(None),
):
    base = select(Species.id)
    if smiles is not None:
        base = base.where(Species.smiles == smiles)
    if inchi_key is not None:
        base = base.where(Species.inchi_key == inchi_key)
    if charge is not None:
        base = base.where(Species.charge == charge)
    if multiplicity is not None:
        base = base.where(Species.multiplicity == multiplicity)
    if kind is not None:
        base = base.where(Species.kind == kind)

    total = session.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    rows = session.scalars(
        select(Species)
        .where(Species.id.in_(base))
        .order_by(Species.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[SpeciesRead.model_validate(r) for r in rows],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{species_id}", response_model=SpeciesRead)
def get_species(species_id: int, session: Session = Depends(get_db)):
    species = session.get(Species, species_id)
    if species is None:
        raise NotFoundError(f"Species {species_id} not found")
    return SpeciesRead.model_validate(species)


# ---------------------------------------------------------------------------
# Species entries (mounted under /species-entries in router.py)
# ---------------------------------------------------------------------------

entries_router = APIRouter()


@entries_router.get("/{entry_id}", response_model=SpeciesEntryRead)
def get_species_entry(entry_id: int, session: Session = Depends(get_db)):
    entry = session.get(SpeciesEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"SpeciesEntry {entry_id} not found")
    return SpeciesEntryRead.model_validate(entry)


@entries_router.get(
    "/{entry_id}/conformers",
    response_model=list[ConformerObservationRead],
)
def list_conformers_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(SpeciesEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"SpeciesEntry {entry_id} not found")
    observations = session.scalars(
        select(ConformerObservation)
        .join(ConformerGroup)
        .where(ConformerGroup.species_entry_id == entry_id)
        .order_by(ConformerObservation.id)
    ).all()
    return [ConformerObservationRead.model_validate(o) for o in observations]


@entries_router.get(
    "/{entry_id}/thermo",
    response_model=list[ThermoRead],
)
def list_thermo_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(SpeciesEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"SpeciesEntry {entry_id} not found")
    rows = session.scalars(
        select(Thermo)
        .where(Thermo.species_entry_id == entry_id)
        .order_by(Thermo.id)
    ).all()
    return [ThermoRead.model_validate(r) for r in rows]


@entries_router.get(
    "/{entry_id}/statmech",
    response_model=list[StatmechRead],
)
def list_statmech_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(SpeciesEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"SpeciesEntry {entry_id} not found")
    rows = session.scalars(
        select(Statmech)
        .where(Statmech.species_entry_id == entry_id)
        .order_by(Statmech.id)
    ).all()
    return [StatmechRead.model_validate(r) for r in rows]


@entries_router.get(
    "/{entry_id}/transport",
    response_model=list[TransportRead],
)
def list_transport_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(SpeciesEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"SpeciesEntry {entry_id} not found")
    rows = session.scalars(
        select(Transport)
        .where(Transport.species_entry_id == entry_id)
        .options(selectinload(Transport.source_calculations))
        .order_by(Transport.id)
    ).all()
    return [TransportRead.model_validate(r) for r in rows]
