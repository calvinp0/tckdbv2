from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

import app.db.models  # noqa: F401
from app.chemistry.geometry import parse_xyz
from app.db.models.calculation import CalculationOutputGeometry
from app.db.models.common import CalculationGeometryRole
from app.db.models.geometry import Geometry, GeometryAtom
from app.db.models.species import (
    ConformerGroup,
    ConformerObservation,
    SpeciesEntry,
)
from app.resolution.species import resolve_species_entry
from app.schemas.fragments.calculation import (
    CalculationCreateRequest,
    CalculationPayload,
)
from app.schemas.geometry import GeometryPayload
from app.schemas.resources.geometry import GeometryAtomBase, GeometryCreate
from app.schemas.workflows.conformer_upload import ConformerUploadRequest
from app.services.calculation_resolution import (
    persist_calculation,
    resolve_calculation_create_request,
)
from app.services.statmech_resolution import resolve_or_create_statmech


def _geometry_create_from_payload(payload: GeometryPayload) -> GeometryCreate:
    """Translate upload geometry data into a resource-shaped create schema.

    :param payload: Upload-facing geometry payload.
    :returns: ``GeometryCreate`` schema with canonicalized hash and atom rows.
    :raises ValueError: If the XYZ payload is malformed.
    """

    parsed = parse_xyz(payload)
    import hashlib

    geom_hash = hashlib.sha256(parsed.canonical_xyz_text.encode("utf-8")).hexdigest()
    atoms = [
        GeometryAtomBase(atom_index=index, element=element, x=x, y=y, z=z)
        for index, (element, x, y, z) in enumerate(parsed.atoms, start=1)
    ]
    return GeometryCreate(
        natoms=parsed.natoms,
        geom_hash=geom_hash,
        xyz_text=parsed.canonical_xyz_text,
        atoms=atoms,
    )


def resolve_geometry_payload(session: Session, payload: GeometryPayload) -> Geometry:
    """Resolve or create a geometry row from uploaded XYZ text.

    :param session: Active SQLAlchemy session.
    :param payload: Upload-facing geometry payload.
    :returns: Existing or newly created ``Geometry`` row.
    :raises ValueError: If the XYZ payload is malformed.
    """

    geometry_create = _geometry_create_from_payload(payload)

    geometry = session.scalar(
        select(Geometry).where(Geometry.geom_hash == geometry_create.geom_hash)
    )
    if geometry is None:
        geometry = Geometry(
            natoms=geometry_create.natoms,
            geom_hash=geometry_create.geom_hash,
            xyz_text=geometry_create.xyz_text,
        )
        session.add(geometry)
        session.flush()

        for atom in geometry_create.atoms:
            session.add(
                GeometryAtom(
                    geometry_id=geometry.id,
                    atom_index=atom.atom_index,
                    element=atom.element,
                    x=atom.x,
                    y=atom.y,
                    z=atom.z,
                )
            )

        session.flush()

    return geometry


def resolve_conformer_group(
    session: Session,
    species_entry: SpeciesEntry,
    *,
    label: str | None,
    created_by: int | None = None,
) -> ConformerGroup:
    """Resolve or create a conformer group for an uploaded observation.

    :param session: Active SQLAlchemy session.
    :param species_entry: Resolved species entry that owns the conformer group.
    :param label: Optional user-supplied conformer label.
    :param created_by: Optional application user id for new rows.
    :returns: Existing labeled group or a newly created conformer group.

    This is currently a placeholder grouping strategy. A matching non-null label
    reuses an existing group; otherwise a new group is created.
    """

    if label is not None:
        conformer_group = session.scalar(
            select(ConformerGroup).where(
                ConformerGroup.species_entry_id == species_entry.id,
                ConformerGroup.label == label,
            )
        )
        if conformer_group is not None:
            return conformer_group

    conformer_group = ConformerGroup(
        species_entry_id=species_entry.id,
        label=label,
        created_by=created_by,
    )
    session.add(conformer_group)
    session.flush()
    return conformer_group


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
