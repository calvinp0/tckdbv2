"""Transition state read endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import NotFoundError
from app.db.models.transition_state import TransitionState, TransitionStateEntry
from app.schemas.entities.transition_state import (
    TransitionStateEntryRead,
    TransitionStateRead,
)

router = APIRouter()


@router.get("/{ts_id}", response_model=TransitionStateRead)
def get_transition_state(ts_id: int, session: Session = Depends(get_db)):
    ts = session.get(TransitionState, ts_id)
    if ts is None:
        raise NotFoundError(f"TransitionState {ts_id} not found")
    return TransitionStateRead.model_validate(ts)


@router.get(
    "/entries/{entry_id}",
    response_model=TransitionStateEntryRead,
)
def get_transition_state_entry(
    entry_id: int, session: Session = Depends(get_db)
):
    entry = session.get(TransitionStateEntry, entry_id)
    if entry is None:
        raise NotFoundError(f"TransitionStateEntry {entry_id} not found")
    return TransitionStateEntryRead.model_validate(entry)
