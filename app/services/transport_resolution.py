"""Resolution service for transport upload payloads."""

from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.db.models.transport import Transport
from app.schemas.workflows.transport_upload import TransportUploadPayload
from app.services.calculation_resolution import resolve_workflow_tool_release_ref
from app.services.literature_resolution import resolve_or_create_literature
from app.services.software_resolution import resolve_software_release_ref


def resolve_and_create_transport(
    session: Session,
    payload: TransportUploadPayload,
    *,
    species_entry_id: int,
    created_by: int | None = None,
) -> Transport:
    """Resolve provenance refs and create a transport record.

    Always creates a new row — transport records are provenance-bearing
    scientific assertions, and multiple records per species entry are valid.

    :param session: Active SQLAlchemy session.
    :param payload: Upload-facing transport payload with provenance refs.
    :param species_entry_id: Resolved owner species-entry id.
    :param created_by: Optional application user id for the created row.
    :returns: Newly created ``Transport`` row.
    """
    literature = (
        resolve_or_create_literature(session, payload.literature)
        if payload.literature is not None
        else None
    )
    software_release = (
        resolve_software_release_ref(session, payload.software_release)
        if payload.software_release is not None
        else None
    )
    workflow_tool_release = resolve_workflow_tool_release_ref(
        session, payload.workflow_tool_release
    )

    transport = Transport(
        species_entry_id=species_entry_id,
        scientific_origin=payload.scientific_origin,
        literature_id=literature.id if literature else None,
        software_release_id=software_release.id if software_release else None,
        workflow_tool_release_id=(
            workflow_tool_release.id if workflow_tool_release else None
        ),
        sigma_angstrom=payload.sigma_angstrom,
        epsilon_over_k_k=payload.epsilon_over_k_k,
        dipole_debye=payload.dipole_debye,
        polarizability_angstrom3=payload.polarizability_angstrom3,
        rotational_relaxation=payload.rotational_relaxation,
        note=payload.note,
        created_by=created_by,
    )
    session.add(transport)
    session.flush()
    return transport
