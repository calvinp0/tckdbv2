from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Double,
    ForeignKey,
    PrimaryKeyConstraint,
    Text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import (
    ScientificOriginKind,
    ThermoCalculationRole,
    ThermoModelKind,
)

if TYPE_CHECKING:
    from app.db.models.workflow_tool import WorkflowTool

    from app.db.models.calculation import Calculation
    from app.db.models.literature import Literature
    from app.db.models.software import Software
    from app.db.models.species import SpeciesEntry
    from app.db.models.statmech import Statmech


class Thermo(Base, TimestampMixin, CreatedByMixin):
    """Stores curated thermochemistry records for a species entry."""

    __tablename__ = "thermo"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    species_entry_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("species_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    statmech_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("statmech.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    scientific_origin: Mapped[ScientificOriginKind] = mapped_column(
        SAEnum(ScientificOriginKind, name="scientific_origin_kind"), nullable=False
    )

    model_kind: Mapped[ThermoModelKind] = mapped_column(
        SAEnum(ThermoModelKind, name="thermo_model_kind"), nullable=False
    )

    literature_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("literature.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    workflow_tool_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow_tool.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    software_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("software.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    h298_kj_mol: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    s298_j_mol_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    species_entry: Mapped["SpeciesEntry"] = relationship(
        back_populates="thermo_records",
        foreign_keys=[species_entry_id],
    )

    statmech: Mapped[Optional["Statmech"]] = relationship(
        back_populates="thermo_records",
        foreign_keys=[statmech_id],
    )

    points: Mapped[list["ThermoPoint"]] = relationship(
        back_populates="thermo",
        cascade="all, delete-orphan",
        order_by="ThermoPoint.temperature_k",
    )

    nasa: Mapped[Optional["ThermoNASA"]] = relationship(
        back_populates="thermo",
        cascade="all, delete-orphan",
        uselist=False,
    )

    source_calculations: Mapped[list["ThermoSourceCalculation"]] = relationship(
        back_populates="thermo",
        cascade="all, delete-orphan",
    )

    literature: Mapped[Optional["Literature"]] = relationship()
    workflow_tool: Mapped[Optional["WorkflowTool"]] = relationship()
    software: Mapped[Optional["Software"]] = relationship()


class ThermoPoint(Base):
    """Stores tabulated thermodynamic values at a specific temperature."""

    __tablename__ = "thermo_point"

    thermo_id: Mapped[int] = mapped_column(
        ForeignKey("thermo.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    temperature_k: Mapped[float] = mapped_column(Double, nullable=False)

    cp_j_mol_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    h_kj_mol: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    s_j_mol_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    g_kj_mol: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    thermo: Mapped["Thermo"] = relationship(
        back_populates="points",
    )

    __table_args__ = (PrimaryKeyConstraint("thermo_id", "temperature_k"),)


class ThermoNASA(Base):
    """Stores NASA polynomial coefficients for a thermo record."""

    __tablename__ = "thermo_nasa"

    thermo_id: Mapped[int] = mapped_column(
        ForeignKey("thermo.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    t_low_k: Mapped[float] = mapped_column(Double, nullable=False)
    t_mid_k: Mapped[float] = mapped_column(Double, nullable=False)
    t_high_k: Mapped[float] = mapped_column(Double, nullable=False)

    # low-temperature polynomial
    low_a1: Mapped[float] = mapped_column(Double, nullable=False)
    low_a2: Mapped[float] = mapped_column(Double, nullable=False)
    low_a3: Mapped[float] = mapped_column(Double, nullable=False)
    low_a4: Mapped[float] = mapped_column(Double, nullable=False)
    low_a5: Mapped[float] = mapped_column(Double, nullable=False)
    low_a6: Mapped[float] = mapped_column(Double, nullable=False)
    low_a7: Mapped[float] = mapped_column(Double, nullable=False)

    # high-temperature polynomial
    high_a1: Mapped[float] = mapped_column(Double, nullable=False)
    high_a2: Mapped[float] = mapped_column(Double, nullable=False)
    high_a3: Mapped[float] = mapped_column(Double, nullable=False)
    high_a4: Mapped[float] = mapped_column(Double, nullable=False)
    high_a5: Mapped[float] = mapped_column(Double, nullable=False)
    high_a6: Mapped[float] = mapped_column(Double, nullable=False)
    high_a7: Mapped[float] = mapped_column(Double, nullable=False)

    thermo: Mapped["Thermo"] = relationship(
        back_populates="nasa",
    )

    __table_args__ = (
        CheckConstraint("t_low < t_mid", name="thermo_nasa_t_low_lt_t_mid"),
        CheckConstraint("t_mid < t_high", name="thermo_nasa_t_mid_lt_t_high"),
    )


class ThermoSourceCalculation(Base):
    """Links thermo records to the calculations that support them."""

    __tablename__ = "thermo_source_calculation"

    thermo_id: Mapped[int] = mapped_column(
        ForeignKey("thermo.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    role: Mapped[ThermoCalculationRole] = mapped_column(
        SAEnum(ThermoCalculationRole, name="thermo_calc_role"),
        nullable=False,
    )

    thermo: Mapped["Thermo"] = relationship(
        back_populates="source_calculations",
    )

    calculation: Mapped["Calculation"] = relationship()

    __table_args__ = (PrimaryKeyConstraint("thermo_id", "calculation_id", "role"),)
