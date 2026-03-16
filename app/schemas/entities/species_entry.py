from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.db.models.common import (
    SpeciesEntryStateKind,
    SpeciesEntryStereoKind,
    StationaryPointKind,
)
from app.schemas.common import SchemaBase, TimestampedCreatedByReadSchema
from app.schemas.utils import normalize_optional_text

_IDENTITY_TEXT_FIELDS = (
    "unmapped_smiles",
    "stereo_label",
    "electronic_state_label",
    "term_symbol_raw",
    "term_symbol",
    "isotopologue_label",
)


class SpeciesEntryIdentityValidatorMixin:
    @model_validator(mode="after")
    def normalize_identity_text_fields(self) -> Self:
        """Normalize optional identity text fields without imposing stricter semantics yet."""

        for field_name in _IDENTITY_TEXT_FIELDS:
            setattr(
                self,
                field_name,
                normalize_optional_text(getattr(self, field_name, None)),
            )

        return self


class SpeciesEntryBase(SpeciesEntryIdentityValidatorMixin, BaseModel):
    species_id: int
    kind: StationaryPointKind = StationaryPointKind.minimum

    unmapped_smiles: str | None = None

    stereo_kind: SpeciesEntryStereoKind = SpeciesEntryStereoKind.unspecified
    stereo_label: str | None = Field(default=None, max_length=64)

    electronic_state_kind: SpeciesEntryStateKind = SpeciesEntryStateKind.ground
    electronic_state_label: str | None = Field(default=None, max_length=8)

    term_symbol_raw: str | None = Field(default=None, max_length=64)
    term_symbol: str | None = Field(default=None, max_length=64)
    isotopologue_label: str | None = Field(default=None, max_length=64)


class SpeciesEntryCreate(SpeciesEntryBase, SchemaBase):
    pass


class SpeciesEntryUpdate(SpeciesEntryIdentityValidatorMixin, SchemaBase):
    species_id: int | None = None
    kind: StationaryPointKind | None = None

    unmapped_smiles: str | None = None

    stereo_kind: SpeciesEntryStereoKind | None = None
    stereo_label: str | None = Field(default=None, max_length=64)

    electronic_state_kind: SpeciesEntryStateKind | None = None
    electronic_state_label: str | None = Field(default=None, max_length=8)

    term_symbol_raw: str | None = Field(default=None, max_length=64)
    term_symbol: str | None = Field(default=None, max_length=64)
    isotopologue_label: str | None = Field(default=None, max_length=64)


class SpeciesEntryRead(SpeciesEntryBase, TimestampedCreatedByReadSchema):
    pass
