from typing import Self

from pydantic import Field, model_validator

from app.schemas.common import SchemaBase
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.utils import normalize_optional_text


class ReactionParticipantUpload(SchemaBase):
    """Workflow-facing ordered participant slot for a reaction entry.

    :param species_entry_id: Existing species-entry id to reuse directly.
    :param species_entry: Species-entry identity payload to resolve or create.
    :param note: Optional note stored on the structured participant row.
    """

    species_entry_id: int | None = None
    species_entry: SpeciesEntryIdentityPayload | None = None
    note: str | None = None

    @model_validator(mode="after")
    def validate_reference_choice(self) -> Self:
        self.note = normalize_optional_text(self.note)
        if (self.species_entry_id is None) == (self.species_entry is None):
            raise ValueError(
                "Provide exactly one of species_entry_id or species_entry."
            )
        return self


class ReactionUploadRequest(SchemaBase):
    """Workflow-facing reaction upload payload.

    The backend resolves the graph identity into ``ChemReaction`` and
    ``ReactionParticipant`` rows, then creates a new ``ReactionEntry`` with
    ordered structured participants for the resolved species-entry forms.

    :param reversible: Whether the uploaded reaction is reversible.
    :param reactants: Ordered structured participants on the reactant side.
    :param products: Ordered structured participants on the product side.
    """

    reversible: bool
    reactants: list[ReactionParticipantUpload] = Field(min_length=1)
    products: list[ReactionParticipantUpload] = Field(min_length=1)
