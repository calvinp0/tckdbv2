from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CHAR,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.db.base import Base, TimestampMixin, CreatedByMixin
from app.db.models.common import ReactionRole

if TYPE_CHECKING:
    from app.db.models.species import Species
    from app.db.models.transition_state import TransitionState, TransitionStateEntry
    from app.db.models.user import AppUser


class ChemReaction(Base, TimestampMixin):
    __tablename__ = "chem_reaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stoichiometry_hash: Mapped[Optional[str]] = mapped_column(
        CHAR(64), unique=True, nullable=True
    )
    reversible: Mapped[bool] = mapped_column(Boolean, nullable=False)

    participants: Mapped[list["ReactionParticipant"]] = relationship(
        back_populates="reaction",
        cascade="all, delete-orphan",
    )

    entries: Mapped[list["ReactionEntry"]] = relationship(
        back_populates="reaction",
        cascade="all, delete-orphan",
    )

    @property
    def reactants(self) -> list["ReactionParticipant"]:
        return [p for p in self.participants if p.role == ReactionRole.reactant]

    @property
    def products(self) -> list["ReactionParticipant"]:
        return [p for p in self.participants if p.role == ReactionRole.product]


class ReactionParticipant(Base):
    __tablename__ = "reaction_participant"

    reaction_id: Mapped[int] = mapped_column(
        ForeignKey("chem_reaction.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    role: Mapped[ReactionRole] = mapped_column(
        SAEnum(ReactionRole, name="reaction_role"),
        primary_key=True,
    )
    stoichiometry: Mapped[int] = mapped_column(
        SmallInteger, nullable=False
    )
    reaction: Mapped["ChemReaction"] = relationship(
        back_populates="participants",
    )
    species: Mapped["Species"] = relationship(
        back_populates="reaction_participants",
    )


class ReactionEntry(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "reaction_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reaction_id: Mapped[int] = mapped_column(
        ForeignKey("chem_reaction.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    preferred_ts_entry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transition_state_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    reaction: Mapped["ChemReaction"] = relationship(
        back_populates="entries",
    )

    transition_states: Mapped[list["TransitionState"]] = relationship(
        back_populates="reaction_entry",
        cascade="all, delete-orphan",
    )

    preferred_ts_entry: Mapped[Optional["TransitionStateEntry"]] = relationship(
        foreign_keys=[preferred_ts_entry_id],
        post_update=True,
    )
