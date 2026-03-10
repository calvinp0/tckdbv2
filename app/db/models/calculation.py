from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    CheckConstraint,
    Integer,
    UniqueConstraint,
    Boolean,
    Text, CHAR,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import CalculationQuality, CalculationType, CalculationGeometryRole, \
    CalculationDependencyRole, ArtifactKind

if TYPE_CHECKING:
    from app.db.models.species import SpeciesEntry
    from app.db.models.geometry import Geometry


class Calculation(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "calculation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    type: Mapped[CalculationType] = mapped_column(
        SAEnum(CalculationType, name="calc_type"), nullable=False
    )

    quality: Mapped[CalculationQuality] = mapped_column(
        SAEnum(CalculationQuality, name="calculation_quality"),
        nullable=False,
        default=CalculationQuality.raw,
        server_default=CalculationQuality.raw.value,
    )

    species_entry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("species_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    transition_state_entry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transition_state_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    software_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("software.id", deferrable=True, initially="IMMEDIATE"), nullable=True
    )

    workflow_tool_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow_tool.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    lot_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("level_of_theory.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    literature_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("literature.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    species_entry: Mapped[Optional["SpeciesEntry"]] = relationship(
        back_populates="calculations",
        foreign_keys=[species_entry_id],
    )

    transition_state_entry: Mapped[Optional["TransitionStateEntry"]] = relationship(
        back_populates="calculations",
        foreign_keys=[transition_state_entry_id],
    )

    output_geometries: Mapped[list["CalculationOutputGeometry"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
    )

    parent_dependencies: Mapped[list["CalculationDependency"]] = relationship(
        back_populates="parent_calculation",
        foreign_keys="CalculationDependency.parent_calculation_id",
        cascade="all, delete-orphan",
    )

    child_dependencies: Mapped[list["CalculationDependency"]] = relationship(
        back_populates="child_calculation",
        foreign_keys="CalculationDependency.child_calculation_id",
        cascade="all, delete-orphan",
    )

    sp_result: Mapped[Optional["CalculationSPResult"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        uselist=False,
    )

    opt_result: Mapped[Optional["CalculationOptResult"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        uselist=False,
    )

    freq_result: Mapped[Optional["CalculationFreqResult"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        uselist=False,
    )

    artifacts: Mapped[list["CalculationArtifact"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            """
            (species_entry_id IS NOT NULL AND transition_state_entry_id IS NULL)
            OR
            (species_entry_id IS NULL AND transition_state_entry_id IS NOT NULL)
            """,
            name="exactly_one_owner"
        )
    )


class CalculationOutputGeometry(Base):
    __tablename__ = "calculation_output_geometry"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    geometry_id: Mapped[int] = mapped_column(
        ForeignKey("geometry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    output_order: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    role: Mapped[Optional[CalculationGeometryRole]] = mapped_column(
        SAEnum(CalculationGeometryRole, name="calc_geom_role"),
        nullable=True,
    )

    calculation: Mapped["Calculation"] = relationship(
        back_populates="output_geometries",
    )

    geometry: Mapped["Geometry"] = relationship(
        back_populates="calculation_outputs",
    )

    __table_args__ = (
        UniqueConstraint("calculation_id", "geometry_id"),
    )


class CalculationDependency(Base):
    __tablename__ = "calculation_dependency"

    parent_calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    child_calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    dependency_role: Mapped[Optional["CalculationDependencyRole"]] = mapped_column(
        SAEnum(CalculationDependencyRole, name="calc_dependency_role"),
        nullable=True,
    )

    parent_calculation: Mapped["Calculation"] = relationship(
        back_populates="parent_dependencies",
        foreign_keys=[parent_calculation_id],
    )

    child_calculation: Mapped["Calculation"] = relationship(
        back_populates="child_dependencies",
        foreign_keys=[child_calculation_id],
    )

    __table_args__ = (
        CheckConstraint(
            "parent_calculation_id <> child_calculation_id",
            name="calculation_dependency_not_self",
        ),
    )


class CalculationSPResult(Base):
    __tablename__ = "calc_sp_result"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )
    electronic_energy_hartree: Mapped[Optional[float]]

    calculation: Mapped["Calculation"] = relationship(
        back_populates="sp_result",
    )


class CalculationOptResult(Base):
    __tablename__ = "calc_opt_result"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )
    converged: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    n_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_energy_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="opt_results",
    )


class CalculationFreqResults(Base):
    __tablename__ = "calc_freq_results"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )
    n_imag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    img_freq_cm1: Mapped[Optional[float]] = mapped_column(nullable=True)
    zpe_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="freq_results",
    )


class CalculationArtifact(Base, TimestampMixin):
    __tablename__ = "calculation_artifact"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    kind: Mapped[ArtifactKind] = mapped_column(
        SAEnum(ArtifactKind, name="artifact_kind"),
        nullable=False,
    )
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(CHAR(64), nullable=True)
    bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="artifacts",
    )
