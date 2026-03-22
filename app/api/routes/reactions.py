"""Reaction and reaction-entry read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import PaginationParams, get_db
from app.api.errors import NotFoundError
from app.db.models.kinetics import Kinetics
from app.db.models.reaction import ChemReaction, ReactionEntry
from app.db.models.transition_state import TransitionState
from app.schemas.entities.kinetics import KineticsRead
from app.schemas.entities.reaction import ChemReactionRead, ReactionEntryRead
from app.schemas.entities.transition_state import TransitionStateRead
from app.api.routes._pagination import PaginatedResponse

router = APIRouter()


# ---------------------------------------------------------------------------
# Reactions
# ---------------------------------------------------------------------------


@router.get("", response_model=PaginatedResponse[ChemReactionRead])
def list_reactions(
    session: Session = Depends(get_db),
    pagination: PaginationParams = Depends(),
):
    total = session.scalar(select(func.count(ChemReaction.id)))
    rows = session.scalars(
        select(ChemReaction)
        .order_by(ChemReaction.id)
        .offset(pagination.skip)
        .limit(pagination.limit)
    ).all()
    return PaginatedResponse(
        items=[ChemReactionRead.model_validate(r) for r in rows],
        total=total or 0,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{reaction_id}", response_model=ChemReactionRead)
def get_reaction(reaction_id: int, session: Session = Depends(get_db)):
    reaction = session.get(ChemReaction, reaction_id)
    if reaction is None:
        raise NotFoundError(f"Reaction {reaction_id} not found")
    return ChemReactionRead.model_validate(reaction)


# ---------------------------------------------------------------------------
# Reaction entries (mounted under /reaction-entries in router.py)
# ---------------------------------------------------------------------------

entries_router = APIRouter()


@entries_router.get("/{entry_id}", response_model=ReactionEntryRead)
def get_reaction_entry(entry_id: int, session: Session = Depends(get_db)):
    entry = session.get(ReactionEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"ReactionEntry {entry_id} not found")
    return ReactionEntryRead.model_validate(entry)


@entries_router.get(
    "/{entry_id}/kinetics",
    response_model=list[KineticsRead],
)
def list_kinetics_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(ReactionEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"ReactionEntry {entry_id} not found")
    rows = session.scalars(
        select(Kinetics)
        .where(Kinetics.reaction_entry_id == entry_id)
        .order_by(Kinetics.id)
    ).all()
    return [KineticsRead.model_validate(r) for r in rows]


@entries_router.get(
    "/{entry_id}/transition-states",
    response_model=list[TransitionStateRead],
)
def list_transition_states_for_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(ReactionEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"ReactionEntry {entry_id} not found")
    rows = session.scalars(
        select(TransitionState)
        .where(TransitionState.reaction_entry_id == entry_id)
        .order_by(TransitionState.id)
    ).all()
    return [TransitionStateRead.model_validate(r) for r in rows]
