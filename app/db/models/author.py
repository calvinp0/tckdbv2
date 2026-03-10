from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    BigInteger,
    Text,
    CHAR
)
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship,
)

from app.db.base import Base, TimestampMixin, CreatedByMixin

if TYPE_CHECKING:
    from app.db.models.literature_author import LiteratureAuthor


class Author(Base, TimestampMixin):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    given_name: Mapped[Optional[str]] = mapped_column(Text)
    family_name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)

    orcid: Mapped[Optional[str]] = mapped_column(CHAR(19), unique=True)

    literature_links: Mapped[list["LiteratureAuthor"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
    )
