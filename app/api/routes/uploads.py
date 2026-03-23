"""Upload endpoints — the primary write path into TCKDB.

Each route wraps a workflow orchestrator. Transaction management is handled by
the ``get_write_db`` dependency (commit on success, rollback on exception).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_write_db
from app.db.models.app_user import AppUser

# -- Workflow imports --------------------------------------------------------
from app.workflows.conformer import persist_conformer_upload
from app.workflows.kinetics import persist_kinetics_upload
from app.workflows.computed_reaction import persist_computed_reaction_upload
from app.workflows.network import persist_network_upload
from app.workflows.network_pdep import persist_network_pdep_upload
from app.workflows.reaction import persist_reaction_upload
from app.workflows.thermo import persist_thermo_upload
from app.workflows.transition_state import persist_transition_state_upload

# -- Request schema imports --------------------------------------------------
from app.schemas.workflows.conformer_upload import ConformerUploadRequest
from app.schemas.workflows.computed_reaction_upload import ComputedReactionUploadRequest
from app.schemas.workflows.kinetics_upload import KineticsUploadRequest
from app.schemas.workflows.network_pdep_upload import NetworkPDepUploadRequest
from app.schemas.workflows.network_upload import NetworkUploadRequest
from app.schemas.workflows.reaction_upload import ReactionUploadRequest
from app.schemas.workflows.thermo_upload import ThermoUploadRequest
from app.schemas.workflows.transition_state_upload import (
    TransitionStateUploadRequest,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response models (minimal identity + key links)
# ---------------------------------------------------------------------------


class ConformerUploadResult(BaseModel):
    id: int
    type: str = "conformer_observation"
    species_entry_id: int
    conformer_group_id: int


class ReactionUploadResult(BaseModel):
    id: int
    type: str = "reaction_entry"
    reaction_id: int


class KineticsUploadResult(BaseModel):
    id: int
    type: str = "kinetics"
    reaction_entry_id: int


class NetworkUploadResult(BaseModel):
    id: int
    type: str = "network"


class NetworkPDepUploadResult(BaseModel):
    id: int
    type: str = "network_pdep"
    solve_id: int | None = None


class ThermoUploadResult(BaseModel):
    id: int
    type: str = "thermo"
    species_entry_id: int


class TransitionStateUploadResult(BaseModel):
    id: int
    type: str = "transition_state_entry"
    transition_state_id: int
    reaction_entry_id: int


class ComputedReactionUploadResult(BaseModel):
    type: str = "computed_reaction"
    reaction_entry_id: int
    reaction_id: int
    transition_state_entry_id: int | None = None
    kinetics_ids: list[int]
    thermo_ids: list[int]
    species_entry_ids: list[int]
    species_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/conformers",
    response_model=ConformerUploadResult,
    status_code=201,
)
def upload_conformer(
    request: ConformerUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    observation = persist_conformer_upload(
        session, request, created_by=current_user.id
    )
    return ConformerUploadResult(
        id=observation.id,
        species_entry_id=observation.conformer_group.species_entry_id,
        conformer_group_id=observation.conformer_group_id,
    )


@router.post(
    "/reactions",
    response_model=ReactionUploadResult,
    status_code=201,
)
def upload_reaction(
    request: ReactionUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    reaction_entry = persist_reaction_upload(
        session, request, created_by=current_user.id
    )
    return ReactionUploadResult(
        id=reaction_entry.id,
        reaction_id=reaction_entry.reaction_id,
    )


@router.post(
    "/kinetics",
    response_model=KineticsUploadResult,
    status_code=201,
)
def upload_kinetics(
    request: KineticsUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    kinetics = persist_kinetics_upload(
        session, request, created_by=current_user.id
    )
    return KineticsUploadResult(
        id=kinetics.id,
        reaction_entry_id=kinetics.reaction_entry_id,
    )


@router.post(
    "/networks",
    response_model=NetworkUploadResult,
    status_code=201,
)
def upload_network(
    request: NetworkUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    network = persist_network_upload(
        session, request, created_by=current_user.id
    )
    return NetworkUploadResult(id=network.id)


@router.post(
    "/networks/pdep",
    response_model=NetworkPDepUploadResult,
    status_code=201,
)
def upload_network_pdep(
    request: NetworkPDepUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    network = persist_network_pdep_upload(
        session, request, created_by=current_user.id
    )
    solve_id = network.solves[0].id if network.solves else None
    return NetworkPDepUploadResult(id=network.id, solve_id=solve_id)


@router.post(
    "/thermo",
    response_model=ThermoUploadResult,
    status_code=201,
)
def upload_thermo(
    request: ThermoUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    thermo = persist_thermo_upload(
        session, request, created_by=current_user.id
    )
    return ThermoUploadResult(
        id=thermo.id,
        species_entry_id=thermo.species_entry_id,
    )


@router.post(
    "/transition-states",
    response_model=TransitionStateUploadResult,
    status_code=201,
)
def upload_transition_state(
    request: TransitionStateUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    ts_entry = persist_transition_state_upload(
        session, request, created_by=current_user.id
    )
    return TransitionStateUploadResult(
        id=ts_entry.id,
        transition_state_id=ts_entry.transition_state_id,
        reaction_entry_id=ts_entry.transition_state.reaction_entry_id,
    )


@router.post(
    "/computed-reaction",
    response_model=ComputedReactionUploadResult,
    status_code=201,
)
def upload_computed_reaction(
    request: ComputedReactionUploadRequest,
    session: Session = Depends(get_write_db),
    current_user: AppUser = Depends(get_current_user),
):
    result = persist_computed_reaction_upload(
        session, request, created_by=current_user.id
    )
    return ComputedReactionUploadResult(**result)
