from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import (
    RigidRotorKind,
    ScientificOriginKind,
    StatmechCalculationRole,
    StatmechTreatmentKind,
    TorsionTreatmentKind,
)

if TYPE_CHECKING:
    from app.db.models.workflow_tool import WorkflowTool

    from app.db.models.calculation import Calculation
    from app.db.models.literature import Literature
    from app.db.models.software import Software
    from app.db.models.species import SpeciesEntry
    from app.db.models.thermo import Thermo


class Statmech(Base, TimestampMixin, CreatedByMixin):
    """Stores statistical mechanics metadata for a species entry."""

    __tablename__ = "statmech"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    species_entry_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("species_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    scientific_origin: Mapped[ScientificOriginKind] = mapped_column(
        SAEnum(ScientificOriginKind, name="scientific_origin_kind"),
        nullable=False,
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
    )

    external_symmetry: Mapped[Optional[int]] = mapped_column(
        SmallInteger, nullable=True
    )
    point_group: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_linear: Mapped[Optional[bool]] = mapped_column(nullable=True)

    rigid_rotor_kind: Mapped[Optional[RigidRotorKind]] = mapped_column(
        SAEnum(RigidRotorKind, name="rigid_rotor_kind"), nullable=True
    )

    statmech_treatment: Mapped[Optional[StatmechTreatmentKind]] = mapped_column(
        SAEnum(StatmechTreatmentKind, name="statmech_treatment_kind"),
        nullable=True,
    )

    freq_scale_factor: Mapped[Optional[float]] = mapped_column(nullable=True)
    uses_projected_frequencies: Mapped[Optional[bool]] = mapped_column(nullable=True)

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    species_entry: Mapped["SpeciesEntry"] = relationship(
        back_populates="statmech_records",
        foreign_keys=[species_entry_id],
    )

    torsions: Mapped[list["StatmechTorsion"]] = relationship(
        back_populates="statmech", cascade="all, delete-orphan"
    )

    thermo_records: Mapped[list["Thermo"]] = relationship(
        back_populates="statmech",
    )

    source_calculations: Mapped[list["StatmechSourceCalculation"]] = relationship(
        back_populates="statmech",
        cascade="all, delete-orphan",
    )

    literature: Mapped[Optional["Literature"]] = relationship()
    workflow_tool: Mapped[Optional["WorkflowTool"]] = relationship()
    software: Mapped[Optional["Software"]] = relationship()

    __table_args__ = (
        CheckConstraint(
            "external_symmetry IS NULL OR external_symmetry >= 1",
            name="statmech_external_symmetry_ge_1",
        ),
        UniqueConstraint(
            "species_entry_id",
            "scientific_origin",
            "workflow_tool_id",
            "software_id",
            "statmech_treatment",
            name="statmech_dedupe_uq",
        ),
    )


class StatmechSourceCalculation(Base):
    """Links statmech records to source calculations by role."""

    __tablename__ = "statmech_source_calculation"

    statmech_id: Mapped[int] = mapped_column(
        ForeignKey("statmech.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    role: Mapped[StatmechCalculationRole] = mapped_column(
        SAEnum(StatmechCalculationRole, name="statmech_calc_role"),
        primary_key=True,
    )

    statmech: Mapped["Statmech"] = relationship(
        back_populates="source_calculations",
    )

    calculation: Mapped["Calculation"] = relationship()


class StatmechTorsion(Base):
    """Stores a torsional mode associated with a statmech record."""

    __tablename__ = "statmech_torsion"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    statmech_id: Mapped[int] = mapped_column(
        ForeignKey("statmech.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    torsion_index: Mapped[int] = mapped_column(Integer, nullable=False)

    symmetry_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    treatment_kind: Mapped[Optional[TorsionTreatmentKind]] = mapped_column(
        SAEnum(TorsionTreatmentKind, name="torsion_treatment_kind"),
        nullable=True,
    )

    dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    top_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invalidated_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_scan_calculation_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    statmech: Mapped["Statmech"] = relationship(
        back_populates="torsions",
    )

    definitions: Mapped[list["StatmechTorsionDefinition"]] = relationship(
        back_populates="torsion",
        cascade="all, delete-orphan",
        order_by="StatmechTorsionDefinition.coordinate_index",
    )

    source_scan_calculation: Mapped[Optional["Calculation"]] = relationship(
        foreign_keys=[source_scan_calculation_id]
    )

    __table_args__ = (
        CheckConstraint("dimension >= 1", name="statmech_torsion_dimension_ge_1"),
    )


class StatmechTorsionDefinition(Base):
    """Defines the atom indices for one torsional coordinate."""

    __tablename__ = "statmech_torsion_definition"

    torsion_id: Mapped[int] = mapped_column(
        ForeignKey("statmech_torsion.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    coordinate_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    atom1_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom2_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom3_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom4_index: Mapped[int] = mapped_column(Integer, nullable=False)

    torsion: Mapped["StatmechTorsion"] = relationship(back_populates="definitions")

    __table_args__ = (
        CheckConstraint(
            "coordinate_index >= 1", name="statmech_torsion_coord_index_ge_1"
        ),
        CheckConstraint("atom1_index >= 1", name="statmech_torsion_atom1_ge_1"),
        CheckConstraint("atom2_index >= 1", name="statmech_torsion_atom2_ge_1"),
        CheckConstraint("atom3_index >= 1", name="statmech_torsion_atom3_ge_1"),
        CheckConstraint("atom4_index >= 1", name="statmech_torsion_atom4_ge_1"),
    )
