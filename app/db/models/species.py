from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import CHAR, BigInteger, ForeignKey, SmallInteger, Text
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import MoleculeKind, ReactionRole, StationaryPointKind
from app.db.types import RDKitMol

if TYPE_CHECKING:
    from app.db.models.calculation import Calculation
    from app.db.models.reaction import ReactionParticipant
    from app.db.models.statmech import Statmech
    from app.db.models.thermo import Thermo


class Species(Base, TimestampMixin):
    """Stores stable species identities independent of specific calculations."""

    __tablename__ = "species"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    kind: Mapped[MoleculeKind] = mapped_column(
        SAEnum(MoleculeKind, name="molecule_kind"), nullable=False
    )
    smiles: Mapped[str] = mapped_column(Text, nullable=False)
    inchi_key: Mapped[str] = mapped_column(CHAR(27), nullable=False)
    charge: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    multiplicity: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    entries: Mapped[list["SpeciesEntry"]] = relationship(
        back_populates="species", cascade="all, delete-orphan"
    )
    reaction_participants: Mapped[list["ReactionParticipant"]] = relationship(
        back_populates="species",
    )
    __table_args__ = UniqueConstraint("inchi_key")

    @property
    def as_reactant_in(self) -> list["ReactionParticipant"]:
        return [
            rp for rp in self.reaction_participants if rp.role == ReactionRole.reactant
        ]

    @property
    def as_product_in(self) -> list["ReactionParticipant"]:
        return [
            rp for rp in self.reaction_participants if rp.role == ReactionRole.product
        ]


class SpeciesEntry(Base, TimestampMixin, CreatedByMixin):
    """Stores a stationary-point realization of a species."""

    __tablename__ = "species_entry"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    species_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("species.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    kind: Mapped[StationaryPointKind] = mapped_column(
        SAEnum(StationaryPointKind, name="stationary_point_kind"), nullable=False
    )
    mol: Mapped[Optional[str]] = mapped_column(RDKitMol(), nullable=True)
    preferred_calculation_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )

    preferred_thermo_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("thermo.id", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )

    preferred_statmech_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("statmech.id", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )

    species: Mapped["Species"] = relationship(back_populates="entries")

    calculations: Mapped[list["Calculation"]] = relationship(
        back_populates="species_entry", foreign_keys="Calculation.species_entry_id"
    )

    preferred_calculation: Mapped[Optional["Calculation"]] = relationship(
        foreign_keys=[preferred_calculation_id], post_update=True
    )

    thermo_records: Mapped[list["Thermo"]] = relationship(
        back_populates="species_entry",
        cascade="all, delete-orphan",
        foreign_keys="Thermo.species_entry_id",
    )

    preferred_thermo: Mapped[Optional["Thermo"]] = relationship(
        foreign_keys=[preferred_thermo_id],
        post_update=True,
    )

    statmech_records: Mapped[list["Statmech"]] = relationship(
        back_populates="species_entry",
        cascade="all, delete-orphan",
        foreign_keys="Statmech.species_entry_id",
    )

    preferred_statmech: Mapped[Optional["Statmech"]] = relationship(
        foreign_keys=[preferred_statmech_id],
        post_update=True,
    )
