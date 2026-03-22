from __future__ import annotations

import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import ColumnElement

import app.db.models  # noqa: F401
from app.db.models.calculation import (
    Calculation,
    CalculationDependency,
    CalculationFreqResult,
    CalculationOptResult,
    CalculationOutputGeometry,
    CalculationSPResult,
)
from app.db.models.common import (
    CalculationDependencyRole,
    CalculationGeometryRole,
    CalculationType,
)
from app.db.models.level_of_theory import LevelOfTheory
from app.db.models.workflow import WorkflowTool, WorkflowToolRelease
from app.schemas.entities.calculation import CalculationCreateResolved
from app.schemas.fragments.calculation import (
    CalculationCreateRequest,
    CalculationWithResultsPayload,
)
from app.schemas.refs import (
    LevelOfTheoryRef,
    WorkflowToolReleaseRef,
)
from app.services.software_resolution import resolve_software_release_ref


def _null_safe_equals(column: ColumnElement, value: str | None) -> ColumnElement[bool]:
    """Build a nullable equality predicate for dedupe lookups.

    :param column: SQLAlchemy column expression to compare.
    :param value: Candidate value, possibly ``None``.
    :returns: ``column IS NULL`` when ``value`` is ``None``, otherwise ``column = value``.
    """

    return column.is_(None) if value is None else column == value


def _level_of_theory_hash(ref: LevelOfTheoryRef) -> str:
    """Compute the canonical level-of-theory hash used for dedupe.

    :param ref: Upload-facing level-of-theory reference.
    :returns: SHA-256 hash of the canonicalized level-of-theory payload.
    """

    payload = {
        "method": ref.method,
        "basis": ref.basis,
        "aux_basis": ref.aux_basis,
        "dispersion": ref.dispersion,
        "solvent": ref.solvent,
        "solvent_model": ref.solvent_model,
        "keywords": ref.keywords,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def resolve_workflow_tool_release_ref(
    session: Session,
    ref: WorkflowToolReleaseRef | None,
) -> WorkflowToolRelease | None:
    """Resolve or create a workflow-tool release row.

    :param session: Active SQLAlchemy session.
    :param ref: Optional upload-facing workflow-tool release reference.
    :returns: Existing/new ``WorkflowToolRelease`` row, or ``None`` when omitted.
    """

    if ref is None:
        return None

    workflow_tool = session.scalar(
        select(WorkflowTool).where(WorkflowTool.name == ref.name)
    )
    if workflow_tool is None:
        workflow_tool = WorkflowTool(name=ref.name)
        session.add(workflow_tool)
        session.flush()

    release = session.scalar(
        select(WorkflowToolRelease).where(
            WorkflowToolRelease.workflow_tool_id == workflow_tool.id,
            _null_safe_equals(WorkflowToolRelease.version, ref.version),
            _null_safe_equals(WorkflowToolRelease.git_commit, ref.git_commit),
        )
    )
    if release is None:
        release = WorkflowToolRelease(
            workflow_tool_id=workflow_tool.id,
            version=ref.version,
            git_commit=ref.git_commit,
            release_date=ref.release_date,
            notes=ref.notes,
        )
        session.add(release)
        session.flush()

    return release


def resolve_level_of_theory_ref(
    session: Session,
    ref: LevelOfTheoryRef,
) -> LevelOfTheory:
    """Resolve or create a level-of-theory row.

    :param session: Active SQLAlchemy session.
    :param ref: Upload-facing level-of-theory reference.
    :returns: Existing or newly created ``LevelOfTheory`` row.
    """

    lot_hash = _level_of_theory_hash(ref)
    level_of_theory = session.scalar(
        select(LevelOfTheory).where(LevelOfTheory.lot_hash == lot_hash)
    )
    if level_of_theory is None:
        level_of_theory = LevelOfTheory(
            method=ref.method,
            basis=ref.basis,
            aux_basis=ref.aux_basis,
            dispersion=ref.dispersion,
            solvent=ref.solvent,
            solvent_model=ref.solvent_model,
            keywords=ref.keywords,
            lot_hash=lot_hash,
        )
        session.add(level_of_theory)
        session.flush()

    return level_of_theory


def resolve_calculation_create_request(
    session: Session,
    request: CalculationCreateRequest,
) -> CalculationCreateResolved:
    """Resolve upload-facing calculation provenance into foreign-key ids.

    :param session: Active SQLAlchemy session.
    :param request: Upload-facing calculation create request.
    :returns: Internal resolved calculation payload with database ids.
    """

    software_release = resolve_software_release_ref(session, request.software_release)
    workflow_tool_release = resolve_workflow_tool_release_ref(
        session, request.workflow_tool_release
    )
    level_of_theory = resolve_level_of_theory_ref(session, request.level_of_theory)

    return CalculationCreateResolved(
        type=request.type,
        quality=request.quality,
        species_entry_id=request.species_entry_id,
        transition_state_entry_id=request.transition_state_entry_id,
        software_release_id=software_release.id,
        workflow_tool_release_id=(
            workflow_tool_release.id if workflow_tool_release else None
        ),
        lot_id=level_of_theory.id,
        literature_id=request.literature_id,
    )


def persist_calculation(
    session: Session,
    resolved: CalculationCreateResolved,
    *,
    created_by: int | None = None,
) -> Calculation:
    """Persist a resolved calculation payload.

    :param session: Active SQLAlchemy session.
    :param resolved: Internal resolved calculation payload.
    :param created_by: Optional application user id for the created row.
    :returns: Newly created ``Calculation`` row.
    """

    calculation = Calculation(
        type=resolved.type,
        quality=resolved.quality,
        species_entry_id=resolved.species_entry_id,
        transition_state_entry_id=resolved.transition_state_entry_id,
        software_release_id=resolved.software_release_id,
        workflow_tool_release_id=resolved.workflow_tool_release_id,
        lot_id=resolved.lot_id,
        literature_id=resolved.literature_id,
        created_by=created_by,
    )
    session.add(calculation)
    session.flush()
    return calculation


# ---------------------------------------------------------------------------
# Generic "calculation + typed results + dependency edges" helpers
# ---------------------------------------------------------------------------


def persist_calculation_result(
    session: Session,
    calculation: Calculation,
    calc_upload: CalculationWithResultsPayload,
) -> None:
    """Persist an optional typed result block for a calculation.

    :param session: Active SQLAlchemy session.
    :param calculation: The owning calculation row.
    :param calc_upload: Upload payload (may have one result block set).
    """

    if calc_upload.opt_result is not None:
        session.add(
            CalculationOptResult(
                calculation_id=calculation.id,
                converged=calc_upload.opt_result.converged,
                n_steps=calc_upload.opt_result.n_steps,
                final_energy_hartree=calc_upload.opt_result.final_energy_hartree,
            )
        )

    if calc_upload.freq_result is not None:
        session.add(
            CalculationFreqResult(
                calculation_id=calculation.id,
                n_imag=calc_upload.freq_result.n_imag,
                imag_freq_cm1=calc_upload.freq_result.imag_freq_cm1,
                zpe_hartree=calc_upload.freq_result.zpe_hartree,
            )
        )

    if calc_upload.sp_result is not None:
        session.add(
            CalculationSPResult(
                calculation_id=calculation.id,
                electronic_energy_hartree=calc_upload.sp_result.electronic_energy_hartree,
            )
        )


# Mapping from calculation type to the dependency role when the child
# depends on the primary calculation.
_DEPENDENCY_ROLE_FOR_TYPE: dict[CalculationType, CalculationDependencyRole] = {
    CalculationType.freq: CalculationDependencyRole.freq_on,
    CalculationType.sp: CalculationDependencyRole.single_point_on,
    CalculationType.irc: CalculationDependencyRole.irc_start,
}


def resolve_and_persist_calculation_with_results(
    session: Session,
    calc_upload: CalculationWithResultsPayload,
    *,
    species_entry_id: int | None = None,
    transition_state_entry_id: int | None = None,
    created_by: int | None = None,
) -> Calculation:
    """Resolve provenance, persist a calculation, and attach typed results.

    :param session: Active SQLAlchemy session.
    :param calc_upload: Upload-facing calculation block with optional results.
    :param species_entry_id: Owner species-entry id (mutually exclusive with TS).
    :param transition_state_entry_id: Owner TS-entry id.
    :param created_by: Optional application user id.
    :returns: Persisted ``Calculation`` row.
    """

    request = CalculationCreateRequest(
        type=calc_upload.type,
        quality=calc_upload.quality,
        species_entry_id=species_entry_id,
        transition_state_entry_id=transition_state_entry_id,
        software_release=calc_upload.software_release,
        workflow_tool_release=calc_upload.workflow_tool_release,
        level_of_theory=calc_upload.level_of_theory,
        literature_id=calc_upload.literature_id,
    )
    resolved = resolve_calculation_create_request(session, request)
    calculation = persist_calculation(session, resolved, created_by=created_by)
    persist_calculation_result(session, calculation, calc_upload)
    return calculation


def persist_additional_calculations(
    session: Session,
    *,
    primary_calc: Calculation,
    additional_uploads: list[CalculationWithResultsPayload],
    geometry_id: int,
    species_entry_id: int | None = None,
    transition_state_entry_id: int | None = None,
    created_by: int | None = None,
) -> list[Calculation]:
    """Persist additional calculations with dependency edges to a primary.

    Creates each additional calculation, links it to the shared output
    geometry, attaches typed results, and wires a ``CalculationDependency``
    edge back to the primary calculation.

    :param session: Active SQLAlchemy session.
    :param primary_calc: The primary calculation row (parent for deps).
    :param additional_uploads: Additional calculation uploads.
    :param geometry_id: Shared output geometry id.
    :param species_entry_id: Owner species-entry id (mutually exclusive with TS).
    :param transition_state_entry_id: Owner TS-entry id.
    :param created_by: Optional application user id.
    :returns: List of newly created ``Calculation`` rows.
    """

    results: list[Calculation] = []
    for calc_upload in additional_uploads:
        child_calc = resolve_and_persist_calculation_with_results(
            session,
            calc_upload,
            species_entry_id=species_entry_id,
            transition_state_entry_id=transition_state_entry_id,
            created_by=created_by,
        )

        session.add(
            CalculationOutputGeometry(
                calculation_id=child_calc.id,
                geometry_id=geometry_id,
                output_order=1,
                role=CalculationGeometryRole.final,
            )
        )

        dep_role = _DEPENDENCY_ROLE_FOR_TYPE.get(calc_upload.type)
        if dep_role is not None:
            session.add(
                CalculationDependency(
                    parent_calculation_id=primary_calc.id,
                    child_calculation_id=child_calc.id,
                    dependency_role=dep_role,
                )
            )

        results.append(child_calc)

    session.flush()
    return results
