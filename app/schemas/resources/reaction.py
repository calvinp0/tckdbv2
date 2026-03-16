from pydantic import BaseModel, Field

from app.db.models.common import ReactionRole
from app.schemas.common import (
    ORMBaseSchema,
    SchemaBase,
    TimestampedCreatedByReadSchema,
    TimestampedReadSchema,
)

# -----------------------------
# ChemReaction (chem_reaction)
# -----------------------------


class ChemReactionBase(BaseModel):
    reversible: bool
    stoichiometry_hash: str | None = Field(default=None, min_length=64, max_length=64)


class ChemReactionCreate(ChemReactionBase, SchemaBase):
    pass


class ChemReactionUpdate(SchemaBase):
    reversible: bool | None = None
    stoichiometry_hash: str | None = Field(default=None, min_length=64, max_length=64)


class ChemReactionRead(ChemReactionBase, TimestampedReadSchema):
    id: int


# ---------------------------------------
# ReactionParticipant (reaction_participant)
# ---------------------------------------


class ReactionParticipantBase(BaseModel):
    reaction_id: int
    species_id: int
    role: ReactionRole
    stoichiometry: int = Field(ge=1)


class ReactionParticipantCreate(ReactionParticipantBase, SchemaBase):
    pass


class ReactionParticipantUpdate(SchemaBase):
    stoichiometry: int | None = Field(default=None, ge=1)


class ReactionParticipantRead(ReactionParticipantBase, ORMBaseSchema):
    pass


# -----------------------------
# ReactionEntry (reaction_entry)
# -----------------------------


class ReactionEntryBase(BaseModel):
    reaction_id: int


class ReactionEntryCreate(ReactionEntryBase, SchemaBase):
    pass


class ReactionEntryUpdate(SchemaBase):
    reaction_id: int | None = None


class ReactionEntryRead(ReactionEntryBase, TimestampedCreatedByReadSchema):
    pass


# ------------------------------------------------------------------
# ReactionEntryStructureParticipant (reaction_entry_structure_participant)
# ------------------------------------------------------------------


class ReactionEntryStructureParticipantBase(BaseModel):
    reaction_entry_id: int
    species_entry_id: int
    role: ReactionRole
    participant_index: int = Field(ge=1)
    note: str | None = None


class ReactionEntryStructureParticipantCreate(
    ReactionEntryStructureParticipantBase, SchemaBase
):
    pass


class ReactionEntryStructureParticipantUpdate(SchemaBase):
    species_entry_id: int | None = None
    role: ReactionRole | None = None
    participant_index: int | None = Field(default=None, ge=1)
    note: str | None = None


class ReactionEntryStructureParticipantRead(
    ReactionEntryStructureParticipantBase, TimestampedCreatedByReadSchema
):
    id: int
