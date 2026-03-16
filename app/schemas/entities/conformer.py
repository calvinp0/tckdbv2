from typing import Any

from pydantic import BaseModel, Field

from app.db.models.common import (
    ConformerAssignmentScopeKind,
    ConformerSelectionKind,
    ScientificOriginKind,
)
from app.schemas.common import (
    SchemaBase,
    TimestampedCreatedByReadSchema,
)

# Conformer Group


class ConformerGroupBase(BaseModel):
    species_entry_id: int
    label: str | None = Field(default=None, max_length=64)
    note: str | None = None


class ConformerGroupCreate(ConformerGroupBase, SchemaBase):
    pass


class ConformerGroupUpdate(SchemaBase):
    species_entry_id: int | None = None
    label: str | None = Field(default=None, max_length=64)
    note: str | None = None


class ConformerGroupRead(ConformerGroupBase, TimestampedCreatedByReadSchema):
    pass


# Conformer Observation


class ConformerObservationBase(BaseModel):
    conformer_group_id: int
    calculation_id: int
    assignment_scheme_id: int | None = None
    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed
    note: str | None = Field(default=None, description="Custom note provided by user")


class ConformerObservationCreate(ConformerObservationBase, SchemaBase):
    pass


class ConformerObservationUpdate(SchemaBase):
    conformer_group_id: int | None = None
    calculation_id: int | None = None
    assignment_scheme_id: int | None = None
    scientific_origin: ScientificOriginKind | None = None
    note: str | None = None


class ConformerObservationRead(
    ConformerObservationBase, TimestampedCreatedByReadSchema
):
    pass


# Conformer Selection


class ConformerSelectionBase(BaseModel):
    conformer_group_id: int
    assignment_scheme_id: int | None = None
    selection_kind: ConformerSelectionKind
    note: str | None = None


class ConformerSelectionCreate(ConformerSelectionBase, SchemaBase):
    pass


class ConformerSelectionUpdate(SchemaBase):
    conformer_group_id: int | None = None
    assignment_scheme_id: int | None = None
    selection_kind: ConformerSelectionKind | None = None
    note: str | None = None


class ConformerSelectionRead(ConformerSelectionBase, TimestampedCreatedByReadSchema):
    pass


class ConformerAssignmentSchemeBase(BaseModel):
    name: str = Field(max_length=128)
    version: str = Field(max_length=64)
    scope: ConformerAssignmentScopeKind = ConformerAssignmentScopeKind.canonical
    description: str | None = None
    parameters_json: dict[str, Any] | None = None
    code_commit: str | None = Field(default=None, max_length=64)
    is_default: bool = False


class ConformerAssignmentSchemeCreate(ConformerAssignmentSchemeBase, SchemaBase):
    pass


class ConformerAssignmentSchemeUpdate(SchemaBase):
    name: str | None = Field(default=None, max_length=128)
    version: str | None = Field(default=None, max_length=64)
    scope: ConformerAssignmentScopeKind | None = None
    description: str | None = None
    parameters_json: dict[str, Any] | None = None
    code_commit: str | None = Field(default=None, max_length=64)
    is_default: bool | None = None


class ConformerAssignmentSchemeRead(
    ConformerAssignmentSchemeBase,
    TimestampedCreatedByReadSchema,
):
    pass
