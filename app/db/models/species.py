from __future__ import annotations

from typing import Optional

from sqlalchemy import (
    CHAR,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.base import Base, TimestampMixin
from app.db.models.common import MoleculeKind, StationaryPointKind
from app.db.types import RDKitMol


class Species(Base, TimestampMixin):
    __tablename__ = "species"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
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

    __table_args__ = UniqueConstraint("inchi_key")


class SpeciesEntry(Base, TimestampMixin):
    __tablename__ = "species_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", deferrable=True, initially="IMMEDIATE"), nullable=False
    )
    kind: Mapped[StationaryPointKind] = mapped_column(
        SAEnum(StationaryPointKind, name="stationary_point_kind"), nullable=False
    )
    mol: Mapped[Optional[str]] = mapped_column(RDKitMol(), nullable=True)
    preferred_calculation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="DEFERRED"),
        nullable=True,
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("app_user.id", deferrable=True, initially="IMMEDIATE"), nullable=True
    )

    species: Mapped["Species"] = relationship(back_populates="entries")

    calculations: Mapped[list["Calculation"]] = relationship(
        back_populates="species_entry", foreign_keys="Calculation.species_entry_id"
    )

    preferred_calculation: Mapped[Optional["Calculation"]] = relationship(
        foreign_keys=[preferred_calculation_id], post_update=True
    )
