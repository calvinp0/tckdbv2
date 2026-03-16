from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import KineticsModelKind, ScientificOriginKind
from app.schemas.common import SchemaBase
from app.schemas.refs import SoftwareReleaseRef, WorkflowToolReleaseRef
from app.schemas.fragments.identity import SpeciesEntryIdentityPayload
from app.schemas.utils import normalize_optional_text
from app.schemas.workflows.literature_submission import LiteratureSubmissionRequest


class KineticsReactionParticipantUpload(SchemaBase):
    """Workflow-facing ordered participant slot for a kinetics upload.

    :param species_entry: Species-entry identity payload to resolve or create.
    :param note: Optional note stored on the structured participant row.
    """

    species_entry: SpeciesEntryIdentityPayload
    note: str | None = None

    @model_validator(mode="after")
    def normalize_note(self) -> Self:
        self.note = normalize_optional_text(self.note)
        return self


class KineticsReactionUpload(SchemaBase):
    """Workflow-facing reaction content embedded in a kinetics upload.

    :param reversible: Whether the uploaded reaction is reversible.
    :param reactants: Ordered structured participants on the reactant side.
    :param products: Ordered structured participants on the product side.
    """

    reversible: bool
    reactants: list[KineticsReactionParticipantUpload] = Field(min_length=1)
    products: list[KineticsReactionParticipantUpload] = Field(min_length=1)


class KineticsUploadRequest(SchemaBase):
    """Workflow-facing kinetics upload payload.

    The backend resolves reaction identity/entry, optional literature, and
    optional software/workflow provenance, then creates the kinetics row.

    :param reaction: Workflow reaction payload used to resolve/create a reaction entry.
    :param scientific_origin: Scientific origin category for this kinetics record.
    :param model_kind: Kinetics functional form.
    :param literature: Optional literature submission payload.
    :param software_release: Optional software provenance reference.
    :param workflow_tool_release: Optional workflow-tool provenance reference.
    :param a: Optional Arrhenius pre-exponential factor.
    :param a_units: Optional units for the pre-exponential factor.
    :param n: Optional temperature exponent.
    :param ea_kj_mol: Optional activation energy in kJ/mol.
    :param tmin_k: Optional minimum valid temperature in K.
    :param tmax_k: Optional maximum valid temperature in K.
    :param degeneracy: Optional reaction-path degeneracy.
    :param tunneling_model: Optional tunneling model label.
    :param note: Optional free-text note.
    """

    reaction: KineticsReactionUpload
    scientific_origin: ScientificOriginKind
    model_kind: KineticsModelKind = KineticsModelKind.modified_arrhenius

    literature: LiteratureSubmissionRequest | None = None
    software_release: SoftwareReleaseRef | None = None
    workflow_tool_release: WorkflowToolReleaseRef | None = None

    a: float | None = None
    a_units: str | None = None
    n: float | None = None
    ea_kj_mol: float | None = None

    tmin_k: float | None = Field(default=None, gt=0)
    tmax_k: float | None = Field(default=None, gt=0)

    degeneracy: float | None = None
    tunneling_model: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def normalize_optional_text_fields(self) -> Self:
        self.a_units = normalize_optional_text(self.a_units)
        self.tunneling_model = normalize_optional_text(self.tunneling_model)
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
