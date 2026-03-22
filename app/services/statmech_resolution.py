"""Service helpers for creating statmech records.

Statmech is a result table — every upload creates a new row.
No deduplication against existing records.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.db.models.statmech import (
    Statmech,
    StatmechSourceCalculation,
    StatmechTorsion,
    StatmechTorsionDefinition,
)
from app.schemas.workflows.conformer_upload import ConformerUploadStatmechPayload
from app.services.calculation_resolution import resolve_workflow_tool_release_ref
from app.services.software_resolution import resolve_software_release_ref


def resolve_or_create_statmech(
    session: Session,
    payload: ConformerUploadStatmechPayload,
    *,
    species_entry_id: int,
    uploaded_calculation_id: int,
    created_by: int | None = None,
) -> Statmech:
    """Create a statmech record and attach nested provenance.

    Always creates a new row — statmech records are provenance-bearing
    scientific results and multiple records per species entry are valid.

    :param session: Active SQLAlchemy session.
    :param payload: Workflow-facing statmech payload from conformer upload.
    :param species_entry_id: Resolved owner species-entry id.
    :param uploaded_calculation_id: Newly created calculation id from the upload workflow.
    :param created_by: Optional application user id for newly created rows.
    :returns: Newly created ``Statmech`` row with linked sources/torsions.
    """

    software_release = (
        resolve_software_release_ref(session, payload.software_release)
        if payload.software_release is not None
        else None
    )
    workflow_tool_release = resolve_workflow_tool_release_ref(
        session, payload.workflow_tool_release
    )

    statmech = Statmech(
        species_entry_id=species_entry_id,
        scientific_origin=payload.scientific_origin,
        literature_id=payload.literature_id,
        workflow_tool_release_id=(
            workflow_tool_release.id if workflow_tool_release is not None else None
        ),
        software_release_id=(
            software_release.id if software_release is not None else None
        ),
        external_symmetry=payload.external_symmetry,
        point_group=payload.point_group,
        is_linear=payload.is_linear,
        rigid_rotor_kind=payload.rigid_rotor_kind,
        statmech_treatment=payload.statmech_treatment,
        freq_scale_factor=payload.freq_scale_factor,
        uses_projected_frequencies=payload.uses_projected_frequencies,
        note=payload.note,
        created_by=created_by,
    )
    session.add(statmech)
    session.flush()

    # Attach source calculations
    if payload.uploaded_calculation_role is not None:
        session.add(
            StatmechSourceCalculation(
                statmech_id=statmech.id,
                calculation_id=uploaded_calculation_id,
                role=payload.uploaded_calculation_role,
            )
        )

    for source in payload.source_calculations:
        session.add(
            StatmechSourceCalculation(
                statmech_id=statmech.id,
                calculation_id=source.calculation_id,
                role=source.role,
            )
        )

    # Attach torsions and coordinates
    for torsion_payload in payload.torsions:
        torsion = StatmechTorsion(
            statmech_id=statmech.id,
            torsion_index=torsion_payload.torsion_index,
            symmetry_number=torsion_payload.symmetry_number,
            treatment_kind=torsion_payload.treatment_kind,
            dimension=torsion_payload.dimension,
            top_description=torsion_payload.top_description,
            invalidated_reason=torsion_payload.invalidated_reason,
            note=torsion_payload.note,
            source_scan_calculation_id=torsion_payload.source_scan_calculation_id,
        )
        session.add(torsion)
        session.flush()

        for coordinate_payload in torsion_payload.coordinates:
            session.add(
                StatmechTorsionDefinition(
                    torsion_id=torsion.id,
                    coordinate_index=coordinate_payload.coordinate_index,
                    atom1_index=coordinate_payload.atom1_index,
                    atom2_index=coordinate_payload.atom2_index,
                    atom3_index=coordinate_payload.atom3_index,
                    atom4_index=coordinate_payload.atom4_index,
                )
            )

    session.flush()
    return statmech
