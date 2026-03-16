from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.db.models.calculation import CalculationOutputGeometry
from app.db.models.common import CalculationGeometryRole
from app.db.models.species import ConformerObservation
from app.resolution.conformer import resolve_conformer_group
from app.resolution.geometry import resolve_geometry_payload
from app.resolution.species import resolve_species_entry
from app.schemas.fragments.calculation import (
    CalculationCreateRequest,
    CalculationPayload,
)
from app.schemas.workflows.conformer_upload import ConformerUploadRequest
from app.services.calculation_resolution import (
    persist_calculation,
    resolve_calculation_create_request,
)
from app.services.statmech_resolution import resolve_or_create_statmech


def _calculation_request_from_upload(
    payload: CalculationPayload,
    *,
    species_entry_id: int,
) -> CalculationCreateRequest:
    """Translate upload calculation data into a calculation-request payload.

    :param payload: Upload-facing calculation provenance payload.
    :param species_entry_id: Resolved owner species-entry id.
    :returns: Calculation create request for the calculation resolver service.
    """

    return CalculationCreateRequest(
        type=payload.type,
        quality=payload.quality,
        species_entry_id=species_entry_id,
        software_release=payload.software_release,
        workflow_tool_release=payload.workflow_tool_release,
        level_of_theory=payload.level_of_theory,
        literature_id=payload.literature_id,
    )


def persist_conformer_upload(
    session: Session,
    request: ConformerUploadRequest,
    *,
    created_by: int | None = None,
) -> ConformerObservation:
    """Persist a complete conformer upload workflow.

    :param session: Active SQLAlchemy session.
    :param request: Upload-facing conformer payload.
    :param created_by: Optional application user id for newly created rows.
    :returns: Newly created ``ConformerObservation`` row.
    :raises ValueError:
        If species identity or geometry parsing fails during upload resolution.
    """

    species_entry = resolve_species_entry(
        session, request.species_entry, created_by=created_by
    )
    geometry = resolve_geometry_payload(session, request.geometry)

    calculation_request = _calculation_request_from_upload(
        request.calculation,
        species_entry_id=species_entry.id,
    )
    calculation_resolved = resolve_calculation_create_request(
        session, calculation_request
    )
    calculation = persist_calculation(
        session,
        calculation_resolved,
        created_by=created_by,
    )

    session.add(
        CalculationOutputGeometry(
            calculation_id=calculation.id,
            geometry_id=geometry.id,
            output_order=1,
            role=CalculationGeometryRole.final,
        )
    )

    conformer_group = resolve_conformer_group(
        session,
        species_entry,
        label=request.label,
        created_by=created_by,
    )
    observation = ConformerObservation(
        conformer_group_id=conformer_group.id,
        calculation_id=calculation.id,
        scientific_origin=request.scientific_origin,
        note=request.note,
        created_by=created_by,
    )
    session.add(observation)

    if request.statmech is not None:
        resolve_or_create_statmech(
            session,
            request.statmech,
            species_entry_id=species_entry.id,
            uploaded_calculation_id=calculation.id,
            created_by=created_by,
        )

    session.flush()
    return observation
