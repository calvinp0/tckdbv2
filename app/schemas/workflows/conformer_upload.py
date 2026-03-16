from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import (
    RigidRotorKind,
    ScientificOriginKind,
    StatmechCalculationRole,
    StatmechTreatmentKind,
)
from app.schemas.common import SchemaBase
from app.schemas.fragments.calculation import CalculationPayload
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.geometry import GeometryPayload
from app.schemas.refs import SoftwareReleaseRef, WorkflowToolReleaseRef
from app.schemas.entities.statmech import (
    StatmechSourceCalculationCreate,
    StatmechTorsionCreate,
)
from app.schemas.utils import normalize_optional_text


class ConformerUploadStatmechPayload(SchemaBase):
    """Workflow-facing statmech payload nested under conformer upload.

    The backend resolves referenced software/workflow provenance, creates or
    reuses the owning ``Statmech`` row for the resolved species entry, and links
    the newly created upload calculation as a source calculation when requested.
    """

    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed

    literature_id: int | None = None
    workflow_tool_release: WorkflowToolReleaseRef | None = None
    software_release: SoftwareReleaseRef | None = None

    external_symmetry: int | None = Field(default=None, ge=1)
    point_group: str | None = None

    is_linear: bool | None = None
    rigid_rotor_kind: RigidRotorKind | None = None
    statmech_treatment: StatmechTreatmentKind | None = None

    freq_scale_factor: float | None = None
    uses_projected_frequencies: bool | None = None
    note: str | None = None

    uploaded_calculation_role: StatmechCalculationRole | None = None
    source_calculations: list[StatmechSourceCalculationCreate] = Field(
        default_factory=list
    )
    torsions: list[StatmechTorsionCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.point_group = normalize_optional_text(self.point_group)
        self.note = normalize_optional_text(self.note)
        return self


class ConformerUploadRequest(SchemaBase):
    """Workflow-facing conformer upload payload.

    The backend resolves the species, species entry, geometry, and calculation
    provenance, then assigns or creates a conformer group and observation row.
    """

    species_entry: SpeciesEntryIdentityPayload
    geometry: GeometryPayload
    calculation: CalculationPayload
    statmech: ConformerUploadStatmechPayload | None = None

    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed
    note: str | None = None
    label: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.note = normalize_optional_text(self.note)
        self.label = normalize_optional_text(self.label)
        return self
