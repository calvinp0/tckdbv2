from __future__ import annotations

import hashlib
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

import app.db.models  # noqa: F401

from app.chemistry.geometry import parse_xyz
from app.chemistry.species import canonical_species_identity
from app.db.models.calculation import CalculationOutputGeometry
from app.db.models.common import CalculationGeometryRole
from app.db.models.geometry import Geometry, GeometryAtom
from app.db.models.species import ConformerGroup, ConformerObservation, Species, SpeciesEntry
from app.schemas.fragments.calculation import CalculationCreateRequest, CalculationPayload
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.geometry import GeometryPayload
from app.schemas.resources.geometry import GeometryAtomBase, GeometryCreate
from app.schemas.workflows.conformer_upload import ConformerUploadRequest
from app.services.calculation_resolution import (
    persist_calculation,
    resolve_calculation_create_request,
)


def _null_safe_equals(column: ColumnElement, value: str | None) -> ColumnElement[bool]:
    """Build a nullable equality predicate for identity lookups.

    :param column: SQLAlchemy column expression to compare.
    :param value: Candidate value, possibly ``None``.
    :returns: ``column IS NULL`` when ``value`` is ``None``, otherwise ``column = value``.
    """

    return column.is_(None) if value is None else column == value


def resolve_species(
    session: Session,
    payload: SpeciesEntryIdentityPayload,
) -> Species:
    """Resolve or create a species row from upload identity data.

    :param session: Active SQLAlchemy session.
    :param payload: Upload-facing species-entry identity payload.
    :returns: Existing or newly created ``Species`` row.
    :raises ValueError: If the payload cannot be canonicalized into a valid species identity.
    """

    canonical_smiles, inchi_key = canonical_species_identity(payload)

    species = session.scalar(select(Species).where(Species.inchi_key == inchi_key))
    if species is None:
        species = Species(
            kind=payload.molecule_kind,
            smiles=canonical_smiles,
            inchi_key=inchi_key,
            charge=payload.charge,
            multiplicity=payload.multiplicity,
        )
        session.add(species)
        session.flush()

    return species


def resolve_species_entry(
    session: Session,
    payload: SpeciesEntryIdentityPayload,
    *,
    created_by: int | None = None,
) -> SpeciesEntry:
    """Resolve or create a species-entry row from upload identity data.

    :param session: Active SQLAlchemy session.
    :param payload: Upload-facing resolved identity payload.
    :param created_by: Optional application user id for new rows.
    :returns: Existing or newly created ``SpeciesEntry`` row.
    :raises ValueError: If the underlying species identity cannot be canonicalized.
    """

    species = resolve_species(session, payload)

    species_entry = session.scalar(
        select(SpeciesEntry).where(
            SpeciesEntry.species_id == species.id,
            SpeciesEntry.kind == payload.species_entry_kind,
            SpeciesEntry.stereo_kind == payload.stereo_kind,
            _null_safe_equals(SpeciesEntry.stereo_label, payload.stereo_label),
            SpeciesEntry.electronic_state_kind == payload.electronic_state_kind,
            _null_safe_equals(
                SpeciesEntry.electronic_state_label,
                payload.electronic_state_label,
            ),
            _null_safe_equals(SpeciesEntry.term_symbol, payload.term_symbol),
            _null_safe_equals(
                SpeciesEntry.isotopologue_label,
                payload.isotopologue_label,
            ),
        )
    )
    if species_entry is None:
        species_entry = SpeciesEntry(
            species_id=species.id,
            kind=payload.species_entry_kind,
            unmapped_smiles=payload.unmapped_smiles,
            stereo_kind=payload.stereo_kind,
            stereo_label=payload.stereo_label,
            electronic_state_kind=payload.electronic_state_kind,
            electronic_state_label=payload.electronic_state_label,
            term_symbol_raw=payload.term_symbol_raw,
            term_symbol=payload.term_symbol,
            isotopologue_label=payload.isotopologue_label,
            created_by=created_by,
        )
        session.add(species_entry)
        session.flush()

    return species_entry


def _geometry_create_from_payload(payload: GeometryPayload) -> GeometryCreate:
    """Translate upload geometry data into a resource-shaped create schema.

    :param payload: Upload-facing geometry payload.
    :returns: ``GeometryCreate`` schema with canonicalized hash and atom rows.
    :raises ValueError: If the XYZ payload is malformed.
    """

    parsed = parse_xyz(payload)
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
    calculation_resolved = resolve_calculation_create_request(session, calculation_request)
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
    session.flush()
    return observation
