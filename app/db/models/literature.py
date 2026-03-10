from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base, CreatedByMixin, TimestampMixin
from app.db.models.common import LiteratureKind

if TYPE_CHECKING:
    from app.db.models.literature_author import LiteratureAuthor


class Literature(Base, TimestampMixin, CreatedByMixin):
    """Stores bibliographic records used as provenance across the schema."""

    __tablename__ = "literature"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    kind: Mapped[LiteratureKind] = mapped_column(
        SAEnum(LiteratureKind, name="literature_kind"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    journal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    volume: Mapped[Optional[str]] = mapped_column(String(20))
    issue: Mapped[Optional[str]] = mapped_column(String(20))
    pages: Mapped[Optional[str]] = mapped_column(String(50))
    article_number: Mapped[Optional[str]] = mapped_column(String(30))

    doi: Mapped[Optional[str]] = mapped_column(Text)
    isbn: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[Optional[str]] = mapped_column(Text)

    publisher: Mapped[Optional[str]] = mapped_column(Text)
    institution: Mapped[Optional[str]] = mapped_column(Text)

    authors: Mapped[list["LiteratureAuthor"]] = relationship(
        back_populates="literature",
        cascade="all, delete-orphan",
        order_by="LiteratureAuthor.author_order",
    )
