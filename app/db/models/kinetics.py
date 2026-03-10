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
    AUnits,
    KineticsCalculationRole,
    KineticsModelKind,
    ScientificOriginKind,
    TunnelingModelKind,
)

if TYPE_CHECKING:
    from app.db.models.workflow_tool import WorkflowToolRelease

    from app.db.models.calculation import Calculation
    from app.db.models.literature import Literature
    from app.db.models.reaction import ReactionEntry
    from app.db.models.software import SoftwareRelease


class Kinetics(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "kinetics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    reaction_entry_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("reaction_entry.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    scientific_origin: Mapped[ScientificOriginKind] = mapped_column(
        SAEnum(ScientificOriginKind, name="scientific_origin_kind"),
        nullable=False,
    )

    model_kind: Mapped[KineticsModelKind] = mapped_column(
        SAEnum(KineticsModelKind, name="kinetics_model_kind"),
        nullable=False,
        default=KineticsModelKind.modified_arrhenius,
        server_default=KineticsModelKind.modified_arrhenius.value,
    )

    literature_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("literature.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    workflow_tool_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow_tool_release.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    software_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("software_release.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    a: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    a_units: Mapped[Optional[AUnits]] = mapped_column(
        SAEnum(AUnits, name="a_units"),
        nullable=True,
    )

    n: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    ea_kj_mol: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    t0_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    tmin_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    tmax_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    degeneracy: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    tunneling_model: Mapped[Optional[TunnelingModelKind]] = mapped_column(
        SAEnum(TunnelingModelKind, name="tunneling_model_kind"),
        nullable=True,
    )

    a_uncertainty: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    n_uncertainty: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    ea_uncertainty_kj_mol: Mapped[Optional[float]] = mapped_column(
        Double, nullable=True
    )

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reaction_entry: Mapped["ReactionEntry"] = relationship(
        back_populates="kinetics_records",
        foreign_keys=[reaction_entry_id],
    )

    source_calculations: Mapped[list["KineticsSourceCalculation"]] = relationship(
        back_populates="kinetics",
        cascade="all, delete-orphan",
    )

    literature: Mapped[Optional["Literature"]] = relationship()
    workflow_tool_release: Mapped[Optional["WorkflowToolRelease"]] = relationship()
    software_release: Mapped[Optional["SoftwareRelease"]] = relationship()

    __table_args__ = (
        CheckConstraint(
            "t0_k IS NULL OR t0_k > 0",
            name="kinetics_t0_k_gt_0",
        ),
        CheckConstraint(
            "tmin_k IS NULL OR tmin_k > 0",
            name="kinetics_tmin_k_gt_0",
        ),
        CheckConstraint(
            "tmax_k IS NULL OR tmax_k > 0",
            name="kinetics_tmax_k_gt_0",
        ),
        CheckConstraint(
            "tmin_k IS NULL OR tmax_k IS NULL OR tmin_k <= tmax_k",
            name="kinetics_tmin_le_tmax",
        ),
        CheckConstraint(
            "degeneracy IS NULL OR degeneracy > 0",
            name="kinetics_degeneracy_gt_0",
        ),
    )


class KineticsSourceCalculation(Base):
    __tablename__ = "kinetics_source_calculation"

    kinetics_id: Mapped[int] = mapped_column(
        ForeignKey("kinetics.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    calculation_id: Mapped[int] = mapped_column(
        ForeignKey("calculation.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    role: Mapped[KineticsCalculationRole] = mapped_column(
        SAEnum(KineticsCalculationRole, name="kinetics_calc_role"),
        nullable=False,
    )

    kinetics: Mapped["Kinetics"] = relationship(
        back_populates="source_calculations",
    )

    calculation: Mapped["Calculation"] = relationship()

    __table_args__ = (PrimaryKeyConstraint("kinetics_id", "calculation_id", "role"),)
