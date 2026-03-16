from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import ScientificOriginKind
from app.schemas.common import SchemaBase
from app.schemas.fragments.calculation import CalculationPayload
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.geometry import GeometryPayload
from app.schemas.utils import normalize_optional_text


class ConformerUploadRequest(SchemaBase):
    """Workflow-facing conformer upload payload.

    The backend resolves the species, species entry, geometry, and calculation
    provenance, then assigns or creates a conformer group and observation row.
    """

    species_entry: SpeciesEntryIdentityPayload
    geometry: GeometryPayload
    calculation: CalculationPayload

    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed
    note: str | None = None
    label: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.note = normalize_optional_text(self.note)
        self.label = normalize_optional_text(self.label)
        return self
