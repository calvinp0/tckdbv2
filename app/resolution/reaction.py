from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Mapping, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.common import ReactionRole
from app.db.models.reaction import ChemReaction, ReactionParticipant
from app.db.models.species import SpeciesEntry


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


def resolve_chem_reaction(
    session: Session,
    *,
    reversible: bool,
    reactant_stoichiometry: Mapping[int, int],
    product_stoichiometry: Mapping[int, int],
) -> ChemReaction:
    """Resolve or create the graph-identity reaction layer for an upload.

    :param session: Active SQLAlchemy session.
    :param reversible: Whether the submitted reaction is reversible.
    :param reactant_stoichiometry: Compressed reactant stoichiometry keyed by ``species_id``.
    :param product_stoichiometry: Compressed product stoichiometry keyed by ``species_id``.
    :returns: Existing or newly created ``ChemReaction`` row.
    """

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
        return chem_reaction

    chem_reaction = ChemReaction(
        reversible=reversible,
        stoichiometry_hash=stoichiometry_hash,
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
