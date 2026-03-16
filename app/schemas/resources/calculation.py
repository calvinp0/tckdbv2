from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.db.models.common import (
    ArtifactKind,
    CalculationDependencyRole,
    CalculationGeometryRole,
    CalculationQuality,
    CalculationType,
)
from app.schemas.common import SchemaBase, TimestampedCreatedByReadSchema, TimestampedReadSchema
from app.schemas.fragments.calculation import CalculationOwnerRequiredMixin


class CalculationCreateResolved(CalculationOwnerRequiredMixin, SchemaBase):
    """Internal calculation payload after scientific references are resolved to ids."""

    type: CalculationType
    quality: CalculationQuality = CalculationQuality.raw

    species_entry_id: int | None = None
    transition_state_entry_id: int | None = None

    software_release_id: int
    workflow_tool_release_id: int | None = None
    lot_id: int

    literature_id: int | None = None


class CalculationUpdate(SchemaBase):
    type: CalculationType | None = None
    quality: CalculationQuality | None = None

    software_release_id: int | None = None
    workflow_tool_release_id: int | None = None
    lot_id: int | None = None

    literature_id: int | None = None


class CalculationRead(TimestampedCreatedByReadSchema):
    type: CalculationType
    quality: CalculationQuality

    species_entry_id: int | None = None
    transition_state_entry_id: int | None = None

    software_release_id: int | None = None
    workflow_tool_release_id: int | None = None
    lot_id: int | None = None

    literature_id: int | None = None


class CalculationInputGeometryBase(BaseModel):
    calculation_id: int
    geometry_id: int
    input_order: int = Field(default=1, ge=1)


class CalculationInputGeometryCreate(CalculationInputGeometryBase, SchemaBase):
    pass


class CalculationInputGeometryUpdate(SchemaBase):
    geometry_id: int | None = None
    input_order: int | None = Field(default=None, ge=1)


class CalculationInputGeometryRead(CalculationInputGeometryBase, BaseModel):
    pass


class CalculationOutputGeometryBase(BaseModel):
    calculation_id: int
    geometry_id: int
    output_order: int = Field(default=1, ge=1)
    role: CalculationGeometryRole | None = None


class CalculationOutputGeometryCreate(CalculationOutputGeometryBase, SchemaBase):
    pass


class CalculationOutputGeometryUpdate(SchemaBase):
    geometry_id: int | None = None
    output_order: int | None = Field(default=None, ge=1)
    role: CalculationGeometryRole | None = None


class CalculationOutputGeometryRead(CalculationOutputGeometryBase, BaseModel):
    pass


class CalculationDependencyBase(BaseModel):
    parent_calculation_id: int
    child_calculation_id: int
    dependency_role: CalculationDependencyRole

    @model_validator(mode="after")
    def validate_not_self_edge(self) -> Self:
        if self.parent_calculation_id == self.child_calculation_id:
            raise ValueError("Calculation dependencies cannot be self-edges")
        return self


class CalculationDependencyCreate(CalculationDependencyBase, SchemaBase):
    pass


class CalculationDependencyUpdate(SchemaBase):
    """Patch schema for routes that already identify the dependency edge by PK."""

    dependency_role: CalculationDependencyRole | None = None


class CalculationDependencyRead(CalculationDependencyBase, BaseModel):
    pass


class CalculationArtifactBase(BaseModel):
    calculation_id: int
    kind: ArtifactKind
    uri: str = Field(min_length=1)
    sha256: str | None = Field(default=None, min_length=64, max_length=64)
    bytes: int | None = Field(default=None, ge=0)


class CalculationArtifactCreate(CalculationArtifactBase, SchemaBase):
    pass


class CalculationArtifactUpdate(SchemaBase):
    kind: ArtifactKind | None = None
    uri: str | None = Field(default=None, min_length=1)
    sha256: str | None = Field(default=None, min_length=64, max_length=64)
    bytes: int | None = Field(default=None, ge=0)


class CalculationArtifactRead(CalculationArtifactBase, TimestampedReadSchema):
    pass


class CalculationSPResultBase(BaseModel):
    calculation_id: int
    electronic_energy_hartree: float | None = None


class CalculationSPResultCreate(CalculationSPResultBase, SchemaBase):
    pass


class CalculationSPResultUpdate(SchemaBase):
    electronic_energy_hartree: float | None = None


class CalculationSPResultRead(CalculationSPResultBase, BaseModel):
    pass


class CalculationOptResultBase(BaseModel):
    calculation_id: int
    converged: bool | None = None
    n_steps: int | None = Field(default=None, ge=0)
    final_energy_hartree: float | None = None


class CalculationOptResultCreate(CalculationOptResultBase, SchemaBase):
    pass


class CalculationOptResultUpdate(SchemaBase):
    converged: bool | None = None
    n_steps: int | None = Field(default=None, ge=0)
    final_energy_hartree: float | None = None


class CalculationOptResultRead(CalculationOptResultBase, BaseModel):
    pass


class CalculationFreqResultBase(BaseModel):
    calculation_id: int
    n_imag: int | None = None
    imag_freq_cm1: float | None = None
    zpe_hartree: float | None = None


class CalculationFreqResultCreate(CalculationFreqResultBase, SchemaBase):
    pass


class CalculationFreqResultUpdate(SchemaBase):
    n_imag: int | None = None
    imag_freq_cm1: float | None = None
    zpe_hartree: float | None = None


class CalculationFreqResultRead(CalculationFreqResultBase, BaseModel):
    pass
