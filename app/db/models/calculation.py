from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
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
    ScanConstraintKind,
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
    scan_result: Mapped[Optional["CalculationScanResult"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        uselist=False,
    )
    scan_coordinates: Mapped[list["CalculationScanCoordinate"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        order_by="CalculationScanCoordinate.coordinate_index",
    )
    scan_constraints: Mapped[list["CalculationScanConstraint"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        order_by="CalculationScanConstraint.constraint_index",
    )
    scan_points: Mapped[list["CalculationScanPoint"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        order_by="CalculationScanPoint.point_index",
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
            name="one_owner",
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
            "calculation_id",
            "geometry_id",
            name="uq_calculation_input_geometry_calculation_id",
        ),
        CheckConstraint("input_order >= 1", name="input_order_ge_1"),
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
            name="uq_calculation_output_geometry_calculation_id",
        ),
        CheckConstraint("output_order >= 1", name="output_order_ge_1"),
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
            name="not_self",
        ),
        Index(
            "uq_calculation_dependency_child_calculation_id_optimized_from",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'optimized_from'"),
        ),
        Index(
            "uq_calculation_dependency_child_calculation_id_freq_on",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'freq_on'"),
        ),
        Index(
            "uq_calculation_dependency_child_calculation_id_single_point_on",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'single_point_on'"),
        ),
        Index(
            "uq_calculation_dependency_child_calculation_id_scan_parent",
            "child_calculation_id",
            unique=True,
            postgresql_where=text("dependency_role = 'scan_parent'"),
        ),
        Index(
            "uq_calculation_dependency_child_calculation_id_neb_parent",
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
        CheckConstraint("n_steps IS NULL OR n_steps >= 0", name="n_steps_ge_0"),
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


class CalculationScanResult(Base):
    """Scan-level metadata for a scan calculation."""

    __tablename__ = "calc_scan_result"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    dimension: Mapped[int] = mapped_column(Integer, nullable=False)
    is_relaxed: Mapped[Optional[bool]] = mapped_column(nullable=True)
    zero_energy_reference_hartree: Mapped[Optional[float]] = mapped_column(
        nullable=True
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="scan_result")
    coordinates: Mapped[list["CalculationScanCoordinate"]] = relationship(
        primaryjoin=(
            "CalculationScanResult.calculation_id == "
            "foreign(CalculationScanCoordinate.calculation_id)"
        ),
        viewonly=True,
        order_by="CalculationScanCoordinate.coordinate_index",
    )
    constraints: Mapped[list["CalculationScanConstraint"]] = relationship(
        primaryjoin=(
            "CalculationScanResult.calculation_id == "
            "foreign(CalculationScanConstraint.calculation_id)"
        ),
        viewonly=True,
        order_by="CalculationScanConstraint.constraint_index",
    )
    points: Mapped[list["CalculationScanPoint"]] = relationship(
        primaryjoin=(
            "CalculationScanResult.calculation_id == "
            "foreign(CalculationScanPoint.calculation_id)"
        ),
        viewonly=True,
        order_by="CalculationScanPoint.point_index",
    )

    __table_args__ = (CheckConstraint("dimension >= 1", name="dimension_ge_1"),)


class CalculationScanCoordinate(Base):
    """Definition of one scanned internal coordinate."""

    __tablename__ = "calc_scan_coordinate"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    coordinate_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    atom1_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom2_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom3_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom4_index: Mapped[int] = mapped_column(Integer, nullable=False)

    resolution_degrees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    symmetry_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="scan_coordinates")
    point_coordinate_values: Mapped[list["CalculationScanPointCoordinateValue"]] = (
        relationship(
            back_populates="coordinate",
            cascade="all, delete-orphan",
            overlaps="coordinate_values,scan_point",
        )
    )

    __table_args__ = (
        CheckConstraint("coordinate_index >= 1", name="coordinate_index_ge_1"),
        CheckConstraint("atom1_index >= 1", name="atom1_index_ge_1"),
        CheckConstraint("atom2_index >= 1", name="atom2_index_ge_1"),
        CheckConstraint("atom3_index >= 1", name="atom3_index_ge_1"),
        CheckConstraint("atom4_index >= 1", name="atom4_index_ge_1"),
        CheckConstraint(
            "resolution_degrees IS NULL OR resolution_degrees >= 1",
            name="resolution_degrees_ge_1",
        ),
        CheckConstraint(
            "symmetry_number IS NULL OR symmetry_number >= 1",
            name="symmetry_number_ge_1",
        ),
    )


class CalculationScanConstraint(Base):
    """Constraint metadata attached to a scan calculation."""

    __tablename__ = "calc_scan_constraint"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    constraint_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    constraint_kind: Mapped[ScanConstraintKind] = mapped_column(
        SAEnum(ScanConstraintKind, name="scan_constraint_kind"),
        nullable=False,
    )
    atom1_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom2_index: Mapped[int] = mapped_column(Integer, nullable=False)
    atom3_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    atom4_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="scan_constraints")

    __table_args__ = (
        CheckConstraint(
            "constraint_index >= 1",
            name="constraint_index_ge_1",
        ),
        CheckConstraint("atom1_index >= 1", name="atom1_index_ge_1"),
        CheckConstraint("atom2_index >= 1", name="atom2_index_ge_1"),
        CheckConstraint(
            "atom3_index IS NULL OR atom3_index >= 1",
            name="atom3_index_ge_1",
        ),
        CheckConstraint(
            "atom4_index IS NULL OR atom4_index >= 1",
            name="atom4_index_ge_1",
        ),
    )


class CalculationScanPoint(Base):
    """One sampled point on a scan surface."""

    __tablename__ = "calc_scan_point"

    calculation_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )
    point_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    electronic_energy_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)
    relative_energy_kj_mol: Mapped[Optional[float]] = mapped_column(nullable=True)
    geometry_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("geometry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    calculation: Mapped["Calculation"] = relationship(back_populates="scan_points")
    geometry: Mapped[Optional["Geometry"]] = relationship()
    coordinate_values: Mapped[list["CalculationScanPointCoordinateValue"]] = (
        relationship(
            back_populates="scan_point",
            cascade="all, delete-orphan",
            overlaps="point_coordinate_values,coordinate",
        )
    )

    __table_args__ = (CheckConstraint("point_index >= 1", name="point_index_ge_1"),)


class CalculationScanPointCoordinateValue(Base):
    """Coordinate values for one sampled scan point."""

    __tablename__ = "calc_scan_point_coordinate_value"

    calculation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    point_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    coordinate_index: Mapped[int] = mapped_column(Integer, primary_key=True)
    angle_degrees: Mapped[float] = mapped_column(nullable=False)

    scan_point: Mapped["CalculationScanPoint"] = relationship(
        back_populates="coordinate_values",
        overlaps="point_coordinate_values,coordinate",
    )
    coordinate: Mapped["CalculationScanCoordinate"] = relationship(
        back_populates="point_coordinate_values",
        overlaps="coordinate_values,scan_point",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["calculation_id", "point_index"],
            ["calc_scan_point.calculation_id", "calc_scan_point.point_index"],
            deferrable=True,
            initially="IMMEDIATE",
        ),
        ForeignKeyConstraint(
            ["calculation_id", "coordinate_index"],
            [
                "calc_scan_coordinate.calculation_id",
                "calc_scan_coordinate.coordinate_index",
            ],
            deferrable=True,
            initially="IMMEDIATE",
        ),
        CheckConstraint(
            "point_index >= 1",
            name="point_index_ge_1",
        ),
        CheckConstraint(
            "coordinate_index >= 1",
            name="coordinate_index_ge_1",
        ),
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

    calculation: Mapped["Calculation"] = relationship(back_populates="artifacts")
