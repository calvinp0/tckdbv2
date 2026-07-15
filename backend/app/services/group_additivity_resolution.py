"""Resolution service for group-additivity (Benson) provenance payloads.

Handles dedup-or-create for GA schemes and creates an applied GA breakdown
(with its per-group components) attached to a persisted ``thermo`` record.
Mirrors ``app.services.energy_correction_resolution``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.group_additivity import (
    AppliedGroupAdditivity,
    AppliedGroupAdditivityComponent,
    GroupAdditivityScheme,
)
from app.schemas.workflows.group_additivity_upload import (
    AppliedGroupAdditivityUploadPayload,
    GroupAdditivitySchemeRef,
)
from app.services.literature_resolution import resolve_or_create_literature


def resolve_or_create_ga_scheme(
    session: Session,
    ref: GroupAdditivitySchemeRef,
    *,
    created_by: int | None = None,
) -> GroupAdditivityScheme:
    """Resolve or create a group-additivity scheme.

    Dedup key: ``(name, version)``. Descriptive fields (``description``,
    ``code_commit``, ``note``) and the literature link are only used when a
    new scheme is created; on a hit the existing row is reused unchanged.

    :param session: Active SQLAlchemy session.
    :param ref: Upload-facing scheme reference.
    :param created_by: Optional application user id.
    :returns: Existing or newly created scheme row.
    """
    existing = session.scalar(
        select(GroupAdditivityScheme).where(
            GroupAdditivityScheme.name == ref.name,
            (
                GroupAdditivityScheme.version == ref.version
                if ref.version is not None
                else GroupAdditivityScheme.version.is_(None)
            ),
        )
    )
    if existing is not None:
        return existing

    literature = (
        resolve_or_create_literature(session, ref.source_literature)
        if ref.source_literature is not None
        else None
    )

    scheme = GroupAdditivityScheme(
        name=ref.name,
        version=ref.version,
        description=ref.description,
        source_literature_id=literature.id if literature else None,
        code_commit=ref.code_commit,
        note=ref.note,
        created_by=created_by,
    )
    session.add(scheme)
    session.flush()
    return scheme


def create_applied_group_additivity(
    session: Session,
    payload: AppliedGroupAdditivityUploadPayload,
    *,
    thermo_id: int,
    created_by: int | None = None,
) -> AppliedGroupAdditivity:
    """Resolve the scheme and create an applied GA breakdown for a thermo row.

    :param session: Active SQLAlchemy session.
    :param payload: Upload-facing applied GA payload.
    :param thermo_id: Id of the (estimated) thermo record this breakdown
        explains. One breakdown per thermo is enforced by the table's UNIQUE
        constraint on ``thermo_id``.
    :param created_by: Optional application user id.
    :returns: Newly created ``AppliedGroupAdditivity`` row.
    """
    scheme = resolve_or_create_ga_scheme(
        session, payload.scheme, created_by=created_by
    )

    applied = AppliedGroupAdditivity(
        thermo_id=thermo_id,
        scheme_id=scheme.id,
        note=payload.note,
        created_by=created_by,
    )
    session.add(applied)
    session.flush()

    for comp in payload.components:
        session.add(
            AppliedGroupAdditivityComponent(
                applied_group_additivity_id=applied.id,
                component_kind=comp.component_kind,
                group_label=comp.group_label,
                count=comp.count,
                h298_contribution_kj_mol=comp.h298_contribution_kj_mol,
                s298_contribution_j_mol_k=comp.s298_contribution_j_mol_k,
                cp298_contribution_j_mol_k=comp.cp298_contribution_j_mol_k,
            )
        )

    session.flush()
    return applied
