from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.transport import Transport

    from app.db.models.calculation import Calculation
    from app.db.models.kinetics import Kinetics
    from app.db.models.network import Network
    from app.db.models.statmech import Statmech
    from app.db.models.thermo import Thermo


class WorkflowTool(Base, TimestampMixin):
    """
    Stable identity of a workflow or orchestration tool.

    Examples include ARC, ARKANE, AutoTST, and T3
    Exact Provenance for a specific used instance is stored in WorkflowToolRelease
    """

    __tablename__ = "workflow_tool"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    releases: Mapped[list["WorkflowToolRelease"]] = relationship(
        back_populates="workflow_tool",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint(
            "name",
            name="workflow_tool_name_uq",
        ),
    )


class WorkflowToolRelease(Base, TimestampMixin):
    """
    Exact provenance of a workflow tool instance.

    This can represent a tagged release, a specific git commit, a branch state,
    or even a locally modified checkout used in a computational workflow.
    """

    __tablename__ = "workflow_tool_release"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    workflow_tool_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("workflow_tool.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(CHAR(40), nullable=True)
    git_branch: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    git_tag: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_dirty: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    workflow_tool: Mapped["WorkflowTool"] = relationship(
        back_populates="releases",
    )

    calculations: Mapped[list["Calculation"]] = relationship(
        back_populates="workflow_tool_release",
    )
    thermo_records: Mapped[list["Thermo"]] = relationship(
        back_populates="workflow_tool_release",
    )
    statmech_records: Mapped[list["Statmech"]] = relationship(
        back_populates="workflow_tool_release",
    )
    transport_records: Mapped[list["Transport"]] = relationship(
        back_populates="workflow_tool_release",
    )
    kinetics_records: Mapped[list["Kinetics"]] = relationship(
        back_populates="workflow_tool_release",
    )
    networks: Mapped[list["Network"]] = relationship(
        back_populates="workflow_tool_release",
    )

    __table_args__ = (
        UniqueConstraint(
            "workflow_tool_id",
            "version",
            "git_commit",
            "git_branch",
            "git_tag",
            "is_dirty",
            name="workflow_tool_release_dedupe_uq",
        ),
    )
