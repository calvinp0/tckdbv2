from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import NetworkSpeciesRole

if TYPE_CHECKING:
    from app.db.models.workflow_tool import WorkflowToolRelease

    from app.db.models.literature import Literature
    from app.db.models.reaction import ReactionEntry
    from app.db.models.software import SoftwareRelease
    from app.db.models.species import Species


class Network(Base, TimestampMixin, CreatedByMixin):
    __tablename__ = "network"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_pressure_dependent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tmin_k: Mapped[Optional[float]] = mapped_column(nullable=True)
    tmax_k: Mapped[Optional[float]] = mapped_column(nullable=True)

    pmin_bar: Mapped[Optional[float]] = mapped_column(nullable=True)
    pmax_bar: Mapped[Optional[float]] = mapped_column(nullable=True)

    maximum_grain_size_kj_mol: Mapped[Optional[float]] = mapped_column(nullable=True)
    minimum_grain_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

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

    literature: Mapped[Optional["Literature"]] = relationship()
    software_release: Mapped[Optional["SoftwareRelease"]] = relationship()
    workflow_tool_release: Mapped[Optional["WorkflowToolRelease"]] = relationship()

    reactions: Mapped[list["NetworkReaction"]] = relationship(
        back_populates="network",
        cascade="all, delete-orphan",
    )

    species_links: Mapped[list["NetworkSpecies"]] = relationship(
        back_populates="network",
        cascade="all, delete-orphan",
    )


class NetworkReaction(Base):
    __tablename__ = "network_reaction"

    network_id: Mapped[int] = mapped_column(
        ForeignKey("network.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    reaction_entry_id: Mapped[int] = mapped_column(
        ForeignKey("reaction_entry.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    network: Mapped["Network"] = relationship(back_populates="reactions")
    reaction_entry: Mapped["ReactionEntry"] = relationship()


class NetworkSpecies(Base):
    __tablename__ = "network_species"

    network_id: Mapped[int] = mapped_column(
        ForeignKey("network.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    species_id: Mapped[int] = mapped_column(
        ForeignKey("species.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    role: Mapped[Optional[NetworkSpeciesRole]] = mapped_column(
        SAEnum(NetworkSpeciesRole, name="network_species_role"),
        nullable=True,
    )

    network: Mapped["Network"] = relationship(back_populates="species_links")
    species: Mapped["Species"] = relationship()
