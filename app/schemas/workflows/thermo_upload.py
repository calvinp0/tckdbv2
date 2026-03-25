"""Upload payload for thermochemistry data attached to a species entry.

The backend resolves provenance refs (literature, software, workflow tool),
creates the ``Thermo`` row with optional child data (tabulated points,
NASA polynomials), and attaches it to the resolved species entry.
"""

from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import ScientificOriginKind
from app.schemas.common import SchemaBase
from app.schemas.entities.thermo import ThermoNASACreate, ThermoPointCreate
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.fragments.refs import SoftwareReleaseRef, WorkflowToolReleaseRef
from app.schemas.utils import normalize_optional_text
from app.schemas.workflows.energy_correction_upload import (
    AppliedEnergyCorrectionUploadPayload,
)
from app.schemas.workflows.literature_upload import LiteratureUploadRequest


class ThermoUploadRequest(SchemaBase):
    """Workflow-facing thermo upload payload.

    The backend resolves the species entry and provenance references,
    then creates a ``Thermo`` row with optional tabulated points,
    NASA polynomial coefficients, and applied energy corrections.
    """

    species_entry: SpeciesEntryIdentityPayload

    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed

    literature: LiteratureUploadRequest | None = None
    software_release: SoftwareReleaseRef | None = None
    workflow_tool_release: WorkflowToolReleaseRef | None = None

    h298_kj_mol: float | None = None
    s298_j_mol_k: float | None = None

    h298_uncertainty_kj_mol: float | None = Field(default=None, ge=0)
    s298_uncertainty_j_mol_k: float | None = Field(default=None, ge=0)

    tmin_k: float | None = Field(default=None, gt=0)
    tmax_k: float | None = Field(default=None, gt=0)

    note: str | None = None

    # Nested child data
    points: list[ThermoPointCreate] = Field(default_factory=list)
    nasa: ThermoNASACreate | None = None

    # Applied energy corrections for this thermo record
    applied_energy_corrections: list[AppliedEnergyCorrectionUploadPayload] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def normalize_text_fields(self) -> Self:
        self.note = normalize_optional_text(self.note)
        return self

    @model_validator(mode="after")
    def validate_temperature_range(self) -> Self:
        if (
            self.tmin_k is not None
            and self.tmax_k is not None
            and self.tmin_k > self.tmax_k
        ):
            raise ValueError("tmin_k must be less than or equal to tmax_k.")
        return self

    @model_validator(mode="after")
    def validate_unique_points(self) -> Self:
        temps = [p.temperature_k for p in self.points]
        if len(set(temps)) != len(temps):
            raise ValueError("Thermo points must be unique by temperature_k.")
        return self
