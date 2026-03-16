from typing import Self

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from app.db.models.common import LiteratureKind
from app.schemas.common import SchemaBase, TimestampedReadSchema
from app.schemas.utils import normalize_optional_text, normalize_required_text


class LiteratureBase(BaseModel):
    kind: LiteratureKind
    title: str = Field(min_length=1)

    journal: str | None = None
    year: int | None = Field(default=None, ge=1, le=3000)
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None

    doi: str | None = None
    isbn: str | None = None
    url: HttpUrl | None = None

    publisher: str | None = None
    institution: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return normalize_required_text(value)

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.journal = normalize_optional_text(self.journal)
        self.volume = normalize_optional_text(self.volume)
        self.issue = normalize_optional_text(self.issue)
        self.pages = normalize_optional_text(self.pages)
        self.doi = normalize_optional_text(self.doi)
        self.isbn = normalize_optional_text(self.isbn)
        self.publisher = normalize_optional_text(self.publisher)
        self.institution = normalize_optional_text(self.institution)
        return self


class LiteratureCreate(LiteratureBase, SchemaBase):
    pass


class LiteratureUpdate(SchemaBase):
    kind: LiteratureKind | None = None
    title: str | None = Field(default=None, min_length=1)

    journal: str | None = None
    year: int | None = Field(default=None, ge=1, le=3000)
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None

    doi: str | None = None
    isbn: str | None = None
    url: HttpUrl | None = None

    publisher: str | None = None
    institution: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_required_text(value)

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.journal = normalize_optional_text(self.journal)
        self.volume = normalize_optional_text(self.volume)
        self.issue = normalize_optional_text(self.issue)
        self.pages = normalize_optional_text(self.pages)
        self.doi = normalize_optional_text(self.doi)
        self.isbn = normalize_optional_text(self.isbn)
        self.publisher = normalize_optional_text(self.publisher)
        self.institution = normalize_optional_text(self.institution)
        return self


class LiteratureRead(LiteratureBase, TimestampedReadSchema):
    pass
