from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

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


def _null_safe_equals(column: ColumnElement, value: int | str | None) -> ColumnElement[bool]:
    """Build a nullable equality predicate for statmech dedupe lookups.

    :param column: SQLAlchemy column expression to compare.
    :param value: Candidate value, possibly ``None``.
    :returns: ``column IS NULL`` when ``value`` is ``None``, otherwise ``column = value``.
    """

    return column.is_(None) if value is None else column == value


def resolve_or_create_statmech(
    session: Session,
    payload: ConformerUploadStatmechPayload,
    *,
    species_entry_id: int,
    uploaded_calculation_id: int,
    created_by: int | None = None,
) -> Statmech:
    """Resolve or create a statmech record and attach nested provenance.

    :param session: Active SQLAlchemy session.
    :param payload: Workflow-facing statmech payload from conformer upload.
    :param species_entry_id: Resolved owner species-entry id.
    :param uploaded_calculation_id: Newly created calculation id from the upload workflow.
    :param created_by: Optional application user id for newly created rows.
    :returns: Existing or newly created ``Statmech`` row with linked sources/torsions.
    """

    software_release = (
        resolve_software_release_ref(session, payload.software_release)
        if payload.software_release is not None
        else None
    )
    workflow_tool_release = resolve_workflow_tool_release_ref(
        session, payload.workflow_tool_release
    )

    statmech = session.scalar(
        select(Statmech).where(
            Statmech.species_entry_id == species_entry_id,
            Statmech.scientific_origin == payload.scientific_origin,
            _null_safe_equals(Statmech.literature_id, payload.literature_id),
            _null_safe_equals(
                Statmech.workflow_tool_release_id,
                workflow_tool_release.id if workflow_tool_release is not None else None,
            ),
            _null_safe_equals(
                Statmech.software_release_id,
                software_release.id if software_release is not None else None,
            ),
            _null_safe_equals(Statmech.statmech_treatment, payload.statmech_treatment),
        )
    )

    if statmech is None:
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

    _attach_statmech_sources(
        session,
        statmech=statmech,
        payload=payload,
        uploaded_calculation_id=uploaded_calculation_id,
    )
    _attach_statmech_torsions(
        session,
        statmech=statmech,
        payload=payload,
        created_by=created_by,
    )
    session.flush()
    return statmech


def _attach_statmech_sources(
    session: Session,
    *,
    statmech: Statmech,
    payload: ConformerUploadStatmechPayload,
    uploaded_calculation_id: int,
) -> None:
    """Attach source-calculation links to a statmech record if they are missing."""

    source_pairs = {
        (source.calculation_id, source.role) for source in statmech.source_calculations
    }

    if payload.uploaded_calculation_role is not None:
        pair = (uploaded_calculation_id, payload.uploaded_calculation_role)
        if pair not in source_pairs:
            session.add(
                StatmechSourceCalculation(
                    statmech_id=statmech.id,
                    calculation_id=uploaded_calculation_id,
                    role=payload.uploaded_calculation_role,
                )
            )
            source_pairs.add(pair)

    for source in payload.source_calculations:
        pair = (source.calculation_id, source.role)
        if pair not in source_pairs:
            session.add(
                StatmechSourceCalculation(
                    statmech_id=statmech.id,
                    calculation_id=source.calculation_id,
                    role=source.role,
                )
            )
            source_pairs.add(pair)


def _attach_statmech_torsions(
    session: Session,
    *,
    statmech: Statmech,
    payload: ConformerUploadStatmechPayload,
    created_by: int | None = None,
) -> None:
    """Attach torsions and coordinates to a statmech record if they are missing."""

    existing_torsions = {torsion.torsion_index: torsion for torsion in statmech.torsions}

    for torsion_payload in payload.torsions:
        torsion = existing_torsions.get(torsion_payload.torsion_index)
        if torsion is None:
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
            existing_torsions[torsion.torsion_index] = torsion

        existing_coordinate_indices = {
            coordinate.coordinate_index for coordinate in torsion.coordinates
        }
        for coordinate_payload in torsion_payload.coordinates:
            if coordinate_payload.coordinate_index in existing_coordinate_indices:
                continue
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
            existing_coordinate_indices.add(coordinate_payload.coordinate_index)
