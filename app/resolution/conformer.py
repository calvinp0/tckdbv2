from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.species import ConformerGroup, SpeciesEntry


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
