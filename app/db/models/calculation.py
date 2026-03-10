from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import (
    ArtifactKind,
    CalculationDependencyRole,
    CalculationGeometryRole,
    CalculationQuality,
    CalculationScanCoordinateKind,
    CalculationScanKind,
    CalculationType,
)

if TYPE_CHECKING:
    from app.db.models.geometry import Geometry
    from app.db.models.species import SpeciesEntry
    from app.db.models.transition_state import TransitionStateEntry


class Calculation(Base, TimestampMixin, CreatedByMixin):
    """Stores one computational job and its provenance links."""

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
        BigInteger,
        ForeignKey("species_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    transition_state_entry_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
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

    scan_result: Mapped[Optional["CalculationScanResult"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
        uselist=False,
    )

    artifacts: Mapped[list["CalculationArtifact"]] = relationship(
        back_populates="calculation",
        cascade="all, delete-orphan",
    )

    __table_args__ = CheckConstraint(
        """
            (species_entry_id IS NOT NULL AND transition_state_entry_id IS NULL)
            OR
            (species_entry_id IS NULL AND transition_state_entry_id IS NOT NULL)
            """,
        name="exactly_one_owner",
    )


class CalculationOutputGeometry(Base):
    """Maps output geometries produced by a calculation."""

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

    __table_args__ = (UniqueConstraint("calculation_id", "geometry_id"),)


class CalculationDependency(Base):
    """Stores directed provenance edges between calculations."""

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
    """Stores single-point energy results for a calculation."""

    __tablename__ = "calc_sp_result"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )
    electronic_energy_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="sp_result",
    )


class CalculationOptResult(Base):
    """Stores optimization-specific results for a calculation."""

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
        back_populates="opt_result",
    )


class CalculationFreqResult(Base):
    """Stores summary vibrational frequency results for a calculation."""

    __tablename__ = "calc_freq_result"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )
    n_imag: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    img_freq_cm1: Mapped[Optional[float]] = mapped_column(nullable=True)
    zpe_hartree: Mapped[Optional[float]] = mapped_column(nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="freq_result",
    )
    modes: Mapped[list["CalculationFreqMode"]] = relationship(
        back_populates="freq_result",
        cascade="all, delete-orphan",
        order_by="CalculationFreqMode.mode_index",
    )
    hessian: Mapped[Optional["CalculationHessian"]] = relationship(
        back_populates="freq_result",
        cascade="all, delete-orphan",
        uselist=False,
    )


class CalculationFreqMode(Base):
    """Stores one vibrational mode belonging to a frequency result."""

    __tablename__ = "calc_freq_mode"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_freq_result.calculation_id", deferrable=True, initially="IMMEDIATE"
        ),
        BigInteger,
        primary_key=True,
    )
    mode_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    frequency_cm1: Mapped[float] = mapped_column(nullable=False)
    reduced_mass_amu: Mapped[Optional[float]] = mapped_column(nullable=True)
    force_constant_mdyn_a: Mapped[Optional[float]] = mapped_column(nullable=True)
    ir_intensity_km_mol: Mapped[Optional[float]] = mapped_column(nullable=True)

    is_scaled: Mapped[Optional[bool]] = mapped_column(nullable=True)
    is_projected: Mapped[Optional[bool]] = mapped_column(nullable=True)

    freq_result: Mapped["CalculationFreqResult"] = relationship(back_populates="modes")

    __table_args__ = (
        CheckConstraint("mode_index >= 1", name="calc_freq_mode_index_ge_1"),
    )


class CalculationHessian(Base):
    """Stores Hessian matrix metadata for a frequency result."""

    __tablename__ = "calc_hessian"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_freq_result.calculation_id", deferrable=True, initially="IMMEDIATE"
        ),
        BigInteger,
        primary_key=True,
    )

    n_atoms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    matrix_dim: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    units: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    representation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifact_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("calculation_artifact.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    freq_result: Mapped["CalculationFreqResult"] = relationship(
        back_populates="hessian",
    )
    artifact: Mapped[Optional["CalculationArtifact"]] = relationship()

    __table_args__ = (
        CheckConstraint(
            "n_atoms IS NULL OR n_atoms >= 1", name="calc_hessian_n_atoms_ge_1"
        ),
        CheckConstraint(
            "matrix_dim IS NULL OR matrix_dim >= 1", name="calc_hessian_matrix_dim_ge_1"
        ),
    )


class CalculationScanResult(Base):
    """Stores summary metadata for a scan calculation."""

    __tablename__ = "calc_scan_result"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        BigInteger,
        primary_key=True,
    )

    scan_kind: Mapped[CalculationScanKind] = mapped_column(
        SAEnum(CalculationScanKind, name="scan_kind"), nullable=False
    )
    dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    n_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    converged: Mapped[Optional[bool]] = mapped_column(nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    calculation: Mapped["Calculation"] = relationship(
        back_populates="scan_result",
    )

    coordinates: Mapped[list["CalculationScanCoordinate"]] = relationship(
        back_populates="scan_result",
        cascade="all, delete-orphan",
        order_by="CalculationScanCoordinate.coordinate_index",
    )

    points: Mapped[list["CalculationScanPoint"]] = relationship(
        back_populates="scan_result",
        cascade="all, delete-orphan",
        order_by="CalculationScanPoint.point_index",
    )

    __table_args__ = (
        CheckConstraint("dimension >= 1", name="calc_scan_dimension_ge_1"),
    )


class CalculationScanCoordinate(Base):
    """Defines one scanned coordinate for a scan calculation."""

    __tablename__ = "calc_scan_coordinate"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_scan_result.calculation_id", deferrable=True, initially="IMMEDIATE"
        ),
        BigInteger,
        primary_key=True,
    )
    coordinate_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    coordinate_kind: Mapped[CalculationScanCoordinateKind] = mapped_column(
        SAEnum(CalculationScanCoordinateKind, name="scan_coordinate_kind"),
        nullable=False,
    )
    atom1_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    atom2_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    atom3_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    atom4_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    symmetry_number: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    top_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    scan_result: Mapped["CalculationScanResult"] = relationship(
        back_populates="coordinates",
    )

    __table_args__ = (
        CheckConstraint(
            "coordinate_index >= 1", name="calc_scan_coordinate_index_ge_1"
        ),
        CheckConstraint(
            "symmetry_number IS NULL OR symmetry_number >= 1",
            name="calc_scan_coord_symmetry_ge_1",
        ),
        CheckConstraint(
            "atom1_index IS NULL OR atom1_index >= 1", name="calc_scan_coord_atom1_ge_1"
        ),
        CheckConstraint(
            "atom2_index IS NULL OR atom2_index >= 1", name="calc_scan_coord_atom2_ge_1"
        ),
        CheckConstraint(
            "atom3_index IS NULL OR atom3_index >= 1", name="calc_scan_coord_atom3_ge_1"
        ),
        CheckConstraint(
            "atom4_index IS NULL OR atom4_index >= 1", name="calc_scan_coord_atom4_ge_1"
        ),
    )


class CalculationScanPoint(Base):
    """Stores one point from a scan calculation profile."""

    __tablename__ = "calc_scan_point"

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_scan_result.calculation_id", deferrable=True, initially="IMMEDIATE"
        ),
        BigInteger,
        primary_key=True,
    )
    point_index: Mapped[int] = mapped_column(Integer, primary_key=True)

    relative_energy_kj_mol: Mapped[Optional[float]] = mapped_column(nullable=True)
    geometry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("geometry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )
    is_valid: Mapped[Optional[bool]] = mapped_column(nullable=True)

    scan_result: Mapped["CalculationScanResult"] = relationship(
        back_populates="points",
    )
    geometry: Mapped[Optional["Geometry"]] = relationship()

    __table_args__ = (
        CheckConstraint("point_index >= 1", name="calc_scan_point_index_ge_1"),
    )


class CalculationArtifact(Base, TimestampMixin):
    """Stores file artifacts emitted or consumed by a calculation."""

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

    __table_args__ = (
        CheckConstraint(
            "bytes IS NULL OR bytes >= 0", name="calculation_artifact_bytes_ge_0"
        ),
    )
