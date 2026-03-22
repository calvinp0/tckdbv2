from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.common import ReactionRole
from app.db.models.reaction import ChemReaction, ReactionFamily, ReactionParticipant
from app.db.models.species import SpeciesEntry
from app.schemas.reaction_family import find_canonical_reaction_family
from app.schemas.utils import normalize_optional_text


def compress_species_stoichiometry(
    species_entries: Sequence[SpeciesEntry],
) -> dict[int, int]:
    """Compress resolved species entries into graph-level stoichiometry counts.

    :param species_entries: Ordered resolved participants on one side of a reaction.
    :returns: Mapping of ``species_id`` to stoichiometric coefficient.
    """

    return dict(Counter(species_entry.species_id for species_entry in species_entries))


def reaction_stoichiometry_hash(
    *,
    reversible: bool,
    reactants: Mapping[int, int],
    products: Mapping[int, int],
) -> str:
    """Build a canonical graph-identity hash for a reaction submission.

    :param reversible: Whether the submitted reaction is reversible.
    :param reactants: Graph-layer reactant stoichiometry keyed by ``species_id``.
    :param products: Graph-layer product stoichiometry keyed by ``species_id``.
    :returns: SHA-256 hash of the canonicalized graph-identity payload.
    """

    payload = {
        "reversible": reversible,
        "reactants": sorted(reactants.items()),
        "products": sorted(products.items()),
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def resolve_reaction_family(
    session: Session,
    reaction_family: str | None,
) -> ReactionFamily | None:
    """Resolve a canonical reaction-family lookup row."""

    canonical_name = find_canonical_reaction_family(reaction_family)
    if canonical_name is None:
        return None

    family = session.scalar(
        select(ReactionFamily).where(ReactionFamily.name == canonical_name)
    )
    if family is not None:
        return family

    raise RuntimeError(
        f"Missing seeded reaction_family row for canonical name {canonical_name!r}."
    )


def resolve_chem_reaction(
    session: Session,
    *,
    reversible: bool,
    reaction_family: str | None = None,
    reaction_family_source_note: str | None = None,
    reactant_stoichiometry: Mapping[int, int],
    product_stoichiometry: Mapping[int, int],
) -> ChemReaction:
    """Resolve or create the graph-identity reaction layer for an upload.

    :param session: Active SQLAlchemy session.
    :param reversible: Whether the submitted reaction is reversible.
    :param reaction_family: Optional reaction-family label using RMG family names.
    :param reaction_family_source_note: Optional provenance note for non-canonical family labels.
    :param reactant_stoichiometry: Compressed reactant stoichiometry keyed by ``species_id``.
    :param product_stoichiometry: Compressed product stoichiometry keyed by ``species_id``.
    :returns: Existing or newly created ``ChemReaction`` row.
    """

    resolved_reaction_family = resolve_reaction_family(session, reaction_family)
    reaction_family_raw = (
        normalize_optional_text(reaction_family)
        if resolved_reaction_family is None
        else None
    )
    normalized_source_note = normalize_optional_text(reaction_family_source_note)

    stoichiometry_hash = reaction_stoichiometry_hash(
        reversible=reversible,
        reactants=reactant_stoichiometry,
        products=product_stoichiometry,
    )
    chem_reaction = session.scalar(
        select(ChemReaction).where(
            ChemReaction.stoichiometry_hash == stoichiometry_hash
        )
    )
    if chem_reaction is not None:
        if resolved_reaction_family is not None:
            if chem_reaction.reaction_family_id is None:
                chem_reaction.reaction_family = resolved_reaction_family
            elif chem_reaction.reaction_family_id != resolved_reaction_family.id:
                raise ValueError(
                    "Resolved reaction already has a different reaction_family: "
                    f"{chem_reaction.reaction_family.name!r} != "
                    f"{resolved_reaction_family.name!r}."
                )
        elif reaction_family_raw is not None:
            if chem_reaction.reaction_family_raw is None:
                chem_reaction.reaction_family_raw = reaction_family_raw
                chem_reaction.reaction_family_source_note = normalized_source_note
            elif chem_reaction.reaction_family_raw != reaction_family_raw:
                raise ValueError(
                    "Resolved reaction already has a different raw reaction_family: "
                    f"{chem_reaction.reaction_family_raw!r} != {reaction_family_raw!r}."
                )
            elif (
                chem_reaction.reaction_family_source_note is None
                and normalized_source_note is not None
            ):
                chem_reaction.reaction_family_source_note = normalized_source_note
        session.flush()
        return chem_reaction

    chem_reaction = ChemReaction(
        reversible=reversible,
        stoichiometry_hash=stoichiometry_hash,
        reaction_family=resolved_reaction_family,
        reaction_family_raw=reaction_family_raw,
        reaction_family_source_note=normalized_source_note,
    )
    session.add(chem_reaction)
    session.flush()

    for species_id, stoichiometry in sorted(reactant_stoichiometry.items()):
        session.add(
            ReactionParticipant(
                reaction_id=chem_reaction.id,
                species_id=species_id,
                role=ReactionRole.reactant,
                stoichiometry=stoichiometry,
            )
        )

    for species_id, stoichiometry in sorted(product_stoichiometry.items()):
        session.add(
            ReactionParticipant(
                reaction_id=chem_reaction.id,
                species_id=species_id,
                role=ReactionRole.product,
                stoichiometry=stoichiometry,
            )
        )

    session.flush()
    return chem_reaction
