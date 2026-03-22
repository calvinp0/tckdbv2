"""Thermo upload workflow orchestrator."""

from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.db.models.thermo import Thermo
from app.schemas.workflows.thermo_upload import ThermoUploadRequest
from app.services.energy_correction_resolution import create_applied_energy_correction
from app.services.species_resolution import resolve_species_entry
from app.services.thermo_resolution import persist_thermo, resolve_thermo_upload


def persist_thermo_upload(
    session: Session,
    request: ThermoUploadRequest,
    *,
    created_by: int | None = None,
) -> Thermo:
    """Persist a complete thermo upload workflow.

    Resolves the species entry, resolves provenance references, creates the
    thermo record with children, and processes any applied energy corrections.

    :param session: Active SQLAlchemy session.
    :param request: Workflow-facing thermo upload payload.
    :param created_by: Optional application user id for newly created rows.
    :returns: Newly created ``Thermo`` row.
    """
    species_entry = resolve_species_entry(
        session, request.species_entry, created_by=created_by
    )

    thermo_create = resolve_thermo_upload(
        session,
        request,
        species_entry_id=species_entry.id,
    )
    thermo = persist_thermo(session, thermo_create, created_by=created_by)

    for correction_payload in request.applied_energy_corrections:
        # source_calculation_key is not resolved here — thermo uploads
        # don't define calculations inline. If the user provides one,
        # it would need to reference an existing calculation id.
        create_applied_energy_correction(
            session,
            correction_payload,
            target_species_entry_id=species_entry.id,
            created_by=created_by,
        )

    session.flush()
    return thermo
