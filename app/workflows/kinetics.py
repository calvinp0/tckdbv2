from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.db.models.kinetics import Kinetics
from app.schemas.workflows.kinetics_upload import KineticsUploadRequest
from app.schemas.workflows.reaction_upload import ReactionUploadRequest
from app.services.kinetics_resolution import persist_kinetics, resolve_kinetics_upload
from app.workflows.reaction import persist_reaction_upload


def persist_kinetics_upload(
    session: Session,
    request: KineticsUploadRequest,
    *,
    created_by: int | None = None,
) -> Kinetics:
    """Persist a complete kinetics upload workflow.

    :param session: Active SQLAlchemy session.
    :param request: Workflow-facing kinetics upload payload.
    :param created_by: Optional application user id for newly created rows.
    :returns: Newly created ``Kinetics`` row attached to a backend-resolved reaction entry.
    """

    reaction_entry = persist_reaction_upload(
        session,
        ReactionUploadRequest(
            reversible=request.reaction.reversible,
            reactants=[
                {
                    "species_entry": participant.species_entry,
                    "note": participant.note,
                }
                for participant in request.reaction.reactants
            ],
            products=[
                {
                    "species_entry": participant.species_entry,
                    "note": participant.note,
                }
                for participant in request.reaction.products
            ],
        ),
        created_by=created_by,
    )
    kinetics_create = resolve_kinetics_upload(
        session,
        request,
        reaction_entry_id=reaction_entry.id,
    )
    return persist_kinetics(session, kinetics_create, created_by=created_by)
