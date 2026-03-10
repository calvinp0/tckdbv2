from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    ForeignKey,
    SmallInteger,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import ReactionRole

if TYPE_CHECKING:
    from app.db.models.kinetics import Kinetics
    from app.db.models.species import Species
    from app.db.models.transition_state import TransitionState, TransitionStateEntry


class ChemReaction(Base, TimestampMixin):
    """Stores a canonical reaction identity and its participants."""

    __tablename__ = "chem_reaction"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
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
    """Represents one species on one side of a reaction."""

    __tablename__ = "reaction_participant"

    reaction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chem_reaction.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    species_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("species.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    role: Mapped[ReactionRole] = mapped_column(
        SAEnum(ReactionRole, name="reaction_role"),
        primary_key=True,
    )
    stoichiometry: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    reaction: Mapped["ChemReaction"] = relationship(
        back_populates="participants",
    )
    species: Mapped["Species"] = relationship(
        back_populates="reaction_participants",
    )


class ReactionEntry(Base, TimestampMixin, CreatedByMixin):
    """Stores an entry-level reaction record and its preferred TS pointer."""

    __tablename__ = "reaction_entry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reaction_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chem_reaction.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    preferred_ts_entry_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("transition_state_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    preferred_kinetics_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("kinetics.id", deferrable=True, initially="DEFERRED"),
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

    kinetics_records: Mapped[list["Kinetics"]] = relationship(
        back_populates="reaction_entry",
        cascade="all, delete-orphan",
        foreign_keys="Kinetics.reaction_entry_id",
    )

    preferred_kinetics: Mapped[Optional["Kinetics"]] = relationship(
        foreign_keys=[preferred_kinetics_id],
        post_update=True,
    )
