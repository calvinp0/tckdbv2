from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, CheckConstraint, Double, ForeignKey, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import ScientificOriginKind

if TYPE_CHECKING:
    from app.db.models.literature import Literature
    from app.db.models.software import SoftwareRelease
    from app.db.models.species import SpeciesEntry
    from app.db.models.workflow import WorkflowToolRelease


class Transport(Base, TimestampMixin, CreatedByMixin):
    """Transport properties attached to a species entry."""

    __tablename__ = "transport"

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

    software_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("software_release.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    workflow_tool_release_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workflow_tool_release.id", deferrable=True, initially="IMMEDIATE"),
        nullable=True,
    )

    sigma_angstrom: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    epsilon_over_k_k: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    dipole_debye: Mapped[Optional[float]] = mapped_column(Double, nullable=True)
    polarizability_angstrom3: Mapped[Optional[float]] = mapped_column(
        Double, nullable=True
    )
    rotational_relaxation: Mapped[Optional[float]] = mapped_column(
        Double, nullable=True
    )

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    species_entry: Mapped["SpeciesEntry"] = relationship(
        back_populates="transport_records"
    )
    literature: Mapped[Optional["Literature"]] = relationship()
    software_release: Mapped[Optional["SoftwareRelease"]] = relationship(
        back_populates="transport_records"
    )
    workflow_tool_release: Mapped[Optional["WorkflowToolRelease"]] = relationship(
        back_populates="transport_records"
    )

    __table_args__ = (
        CheckConstraint(
            "sigma_angstrom IS NULL OR sigma_angstrom > 0",
            name="sigma_angstrom_gt_0",
        ),
        CheckConstraint(
            "epsilon_over_k_k IS NULL OR epsilon_over_k_k > 0",
            name="epsilon_over_k_k_gt_0",
        ),
        CheckConstraint(
            "rotational_relaxation IS NULL OR rotational_relaxation >= 0",
            name="rotational_relaxation_ge_0",
        ),
    )
