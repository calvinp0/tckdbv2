from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    Integer,
    CheckConstraint
)
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
)

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.literature import Literature
    from app.db.models.author import Author


class LiteratureAuthor(Base):
    __tablename__ = "literature_author"

    literature_id: Mapped[int] = mapped_column(
        ForeignKey("literature.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    author_id: Mapped[int] = mapped_column(
        ForeignKey("author.id", deferrable=True, initially="IMMEDIATE"),
        primary_key=True,
    )

    author_order: Mapped[int] = mapped_column(Integer, nullable=False)

    literature: Mapped["Literature"] = relationship(back_populates="authors")
    author: Mapped["Author"] = relationship(back_populates="literature_links")

    __table_args__ = (
        UniqueConstraint("literature_id", "author_order"),
        CheckConstraint(
            "author_order > 0",
            name="author_order_positive"
        )
    )
