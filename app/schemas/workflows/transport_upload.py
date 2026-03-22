"""Shared upload payload for species-level transport properties.

Used by both ``ConformerUploadRequest`` and ``NetworkPDepUploadRequest``.
"""

from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import ScientificOriginKind
from app.schemas.common import SchemaBase
from app.schemas.refs import SoftwareReleaseRef, WorkflowToolReleaseRef
from app.schemas.utils import normalize_optional_text
from app.schemas.workflows.literature_submission import LiteratureSubmissionRequest


class TransportUploadPayload(SchemaBase):
    """Upload payload for species-level transport properties.

    The backend resolves provenance refs and creates a ``Transport`` row
    attached to the resolved species entry.

    :param scientific_origin: Scientific origin category.
    :param literature: Optional literature submission payload.
    :param software_release: Optional software provenance reference.
    :param workflow_tool_release: Optional workflow-tool provenance reference.
    :param sigma_angstrom: Lennard-Jones collision diameter in Å.
    :param epsilon_over_k_k: Lennard-Jones well depth ε/k_B in K.
    :param dipole_debye: Dipole moment in Debye.
    :param polarizability_angstrom3: Polarizability in Å³.
    :param rotational_relaxation: Rotational relaxation collision number (Z_rot).
    :param note: Optional free-text note.
    """

    scientific_origin: ScientificOriginKind = ScientificOriginKind.computed

    literature: LiteratureSubmissionRequest | None = None
    software_release: SoftwareReleaseRef | None = None
    workflow_tool_release: WorkflowToolReleaseRef | None = None

    sigma_angstrom: float | None = Field(default=None, gt=0)
    epsilon_over_k_k: float | None = Field(default=None, gt=0)

    dipole_debye: float | None = None
    polarizability_angstrom3: float | None = None
    rotational_relaxation: float | None = Field(default=None, ge=0)

    note: str | None = None

    @model_validator(mode="after")
    def normalize_text(self) -> Self:
        self.note = normalize_optional_text(self.note)
        return self

    @model_validator(mode="after")
    def validate_lj_pair(self) -> Self:
        """Require Lennard-Jones sigma and epsilon/k to be provided together."""
        if (self.sigma_angstrom is None) != (self.epsilon_over_k_k is None):
            raise ValueError(
                "sigma_angstrom and epsilon_over_k_k must be provided together "
                "or both omitted."
            )
        return self
