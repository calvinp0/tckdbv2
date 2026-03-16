from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import (
    ArtifactKind,
    CalculationDependencyRole,
    CalculationGeometryRole,
    CalculationQuality,
    CalculationType,
)

if TYPE_CHECKING:
    from app.db.models.geometry import Geometry
    from app.db.models.level_of_theory import LevelOfTheory
    from app.db.models.software import SoftwareRelease
    from app.db.models.species import SpeciesEntry
    from app.db.models.transition_state import TransitionStateEntry
    from app.db.models.workflow import WorkflowToolRelease


class Calculation(Base, TimestampMixin, CreatedByMixin):
    """Computational record owned by exactly one species or transition-state entry."""

    __tablename__ = "calculation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    type: Mapped[CalculationType] = mapped_column(
        SAEnum(CalculationType, name="calc_type"),
        nullable=False,
    )
    quality: Mapped[CalculationQuality] = mapped_column(
        SAEnum(CalculationQuality, name="calc_quality"),
        nullable=False,
        default=CalculationQuality.raw,
        server_default=CalculationQuality.raw.value,
    )

    species_entry_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("species_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )
    transition_state_entry_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("transition_state_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    software_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("software_release.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )
    workflow_tool_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow_tool_release.id", deferrable=True, initially="IMMEDIATE"),
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
    software_release: Mapped[Optional["SoftwareRelease"]] = relationship(
        back_populates="calculations"
    )
    workflow_tool_release: Mapped[Optional["WorkflowToolRelease"]] = relationship(
        back_populates="calculations"
    )
    lot: Mapped[Optional["LevelOfTheory"]] = relationship(back_populates="calculations")

    input_geometries: Mapped[list["CalculationInputGeometry"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        order_by="CalculationInputGeometry.input_order",
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
                (
                    transition_state_entry_id IS NOT NULL
                    AND species_entry_id IS NULL
                )
                OR
                (
                    transition_state_entry_id IS NULL
                    AND species_entry_id IS NOT NULL
                )
                """,
            name="exactly_one_owner",
        ),
    )


class CalculationInputGeometry(Base):
    """Ordered input-geometry link table for a calculation."""

    __tablename__ = "calculation_input_geometry"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    geometry_id: Mapped[int] = mapped_column(
        ForeignKey("geometry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    input_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )

    calculation: Mapped["Calculation"] = relationship(back_populates="input_geometries")
    geometry: Mapped["Geometry"] = relationship(back_populates="calculation_inputs")

    __table_args__ = (
        PrimaryKeyConstraint("calculation_id", "input_order"),
        UniqueConstraint(
            "calculation_id", "geometry_id", name="uq_calculation_input_geometry"
        ),
        CheckConstraint("input_order >= 1", name="calculation_input_order_ge_1"),
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
        SAEnum(CalculationGeometryRole, name="calculation_geometry_role"),
        nullable=True,
    )

    calculation: Mapped["Calculation"] = relationship(
        back_populates="output_geometries"
    )
    geometry: Mapped["Geometry"] = relationship(back_populates="calculation_outputs")

    __table_args__ = (
        UniqueConstraint(
            "calculation_id",
            "geometry_id",
            name="uq_calculation_output_geometry_calculation_geometry",
        ),
        CheckConstraint("output_order >= 1", name="calculation_output_order_ge_1"),
    )


class CalculationDependency(Base):
    """Directed dependency edge between two calculations.

    Self-edges are forbidden in the schema. Stronger role-specific parent-count
    rules or full DAG validation belong in application logic unless the policy
    is narrowed enough for partial unique indexes. Selected roles currently
    enforce at most one parent per child: `optimized_from`, `freq_on`,
    `single_point_on`, `scan_parent`, and `neb_parent`.
    """

    __tablename__ = "calculation_dependency"

    parent_calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    child_calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    dependency_role: Mapped[CalculationDependencyRole] = mapped_column(
        SAEnum(CalculationDependencyRole, name="calculation_dependency_role"),
        nullable=False,
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
        Index(
            "calculation_dependency_child_optimized_from_uq",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'optimized_from'"),
        ),
        Index(
            "calculation_dependency_child_freq_on_uq",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'freq_on'"),
        ),
        Index(
            "calculation_dependency_child_single_point_on_uq",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'single_point_on'"),
        ),
        Index(
            "calculation_dependency_child_scan_parent_uq",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'scan_parent'"),
        ),
        Index(
            "calculation_dependency_child_neb_parent_uq",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'neb_parent'"),
        ),
    )


class CalculationSPResult(Base):
    __tablename__ = "calc_sp_result"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    electronic_energy_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="sp_result")


class CalculationOptResult(Base):
    __tablename__ = "calc_opt_result"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    converged: Mapped[Optional[bool]] = mapped_column(nullable=True)
    n_steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_energy_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="opt_result")

    __table_args__ = (
        CheckConstraint(
            "n_steps IS NULL OR n_steps >= 0", name="calc_opt_result_n_steps_ge_0"
        ),
    )


class CalculationFreqResult(Base):
    __tablename__ = "calc_freq_result"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    n_imag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    imag_freq_cm1: Mapped[Optional[float]] = mapped_column(nullable=True)
    zpe_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="freq_result")


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

    calculation: Mapped["Calculation"] = relationship(back_populates="artifacts")
