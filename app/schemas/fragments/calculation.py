from typing import Self

from pydantic import Field, model_validator

from app.db.models.common import CalculationQuality, CalculationType
from app.schemas.common import SchemaBase
from app.schemas.fragments.refs import (
    LevelOfTheoryRef,
    SoftwareReleaseRef,
    WorkflowToolReleaseRef,
)


class CalculationOwnerRequiredMixin:
    """Shared validator for calculation schemas that require exactly one owner."""

    @model_validator(mode="after")
    def validate_exactly_one_owner(self) -> Self:
        owner_count = sum(
            value is not None
            for value in (self.species_entry_id, self.transition_state_entry_id)
        )
        if owner_count != 1:
            raise ValueError(
                "Exactly one of species_entry_id or transition_state_entry_id must be set"
            )
        return self


class CalculationPayload(SchemaBase):
    """Reusable upload fragment for calculation provenance.

    :param type: Calculation type.
    :param quality: Curation quality flag.
    :param software_release: Required software release reference.
    :param workflow_tool_release: Optional workflow tool provenance reference.
    :param level_of_theory: Required level-of-theory reference.
    :param literature_id: Optional literature provenance id.
    """

    type: CalculationType
    quality: CalculationQuality = CalculationQuality.raw

    software_release: SoftwareReleaseRef
    workflow_tool_release: WorkflowToolReleaseRef | None = None
    level_of_theory: LevelOfTheoryRef

    literature_id: int | None = None


# ---------------------------------------------------------------------------
# Typed calculation-result payloads (upload-facing, no FK ids)
# ---------------------------------------------------------------------------


class OptResultPayload(SchemaBase):
    """Optional inline result for an optimisation calculation.

    :param converged: Whether the optimisation converged.
    :param n_steps: Number of optimisation steps.
    :param final_energy_hartree: Final electronic energy in hartree.
    """

    converged: bool | None = None
    n_steps: int | None = Field(default=None, ge=0)
    final_energy_hartree: float | None = None


class FreqResultPayload(SchemaBase):
    """Optional inline result for a frequency calculation.

    :param n_imag: Number of imaginary frequencies.
    :param imag_freq_cm1: Value of the imaginary frequency in cm⁻¹.
    :param zpe_hartree: Zero-point energy in hartree.
    """

    n_imag: int | None = None
    imag_freq_cm1: float | None = None
    zpe_hartree: float | None = None


class SPResultPayload(SchemaBase):
    """Optional inline result for a single-point calculation.

    :param electronic_energy_hartree: Electronic energy in hartree.
    """

    electronic_energy_hartree: float | None = None


class CalculationWithResultsPayload(CalculationPayload):
    """A calculation with optional typed result blocks.

    Extends ``CalculationPayload`` with opt/freq/sp result fields.
    Validation enforces that only the result type matching the calculation
    type may be provided.

    :param opt_result: Inline optimisation result (type must be ``opt``).
    :param freq_result: Inline frequency result (type must be ``freq``).
    :param sp_result: Inline single-point result (type must be ``sp``).
    """

    opt_result: OptResultPayload | None = None
    freq_result: FreqResultPayload | None = None
    sp_result: SPResultPayload | None = None

    @model_validator(mode="after")
    def validate_result_matches_type(self) -> Self:
        """Ensure only the result block matching ``self.type`` is set."""
        allowed = {
            CalculationType.opt: "opt_result",
            CalculationType.freq: "freq_result",
            CalculationType.sp: "sp_result",
        }
        allowed_field = allowed.get(self.type)
        for field_name in ("opt_result", "freq_result", "sp_result"):
            value = getattr(self, field_name)
            if value is not None and field_name != allowed_field:
                raise ValueError(
                    f"Result block '{field_name}' is not allowed for "
                    f"calculation type '{self.type.value}'. "
                    f"Expected '{allowed_field}' or no result."
                )
        return self


# ---------------------------------------------------------------------------
# Internal resolved-calculation request (with FK owner ids)
# ---------------------------------------------------------------------------


class CalculationCreateRequest(CalculationOwnerRequiredMixin, SchemaBase):
    """Reusable upload-oriented request for calculation creation.

    :param type: Calculation type.
    :param quality: Curation quality flag.
    :param species_entry_id: Species-entry owner id when the calculation belongs to a species entry.
    :param transition_state_entry_id: Transition-state-entry owner id when applicable.
    :param software_release: Required software release reference.
    :param workflow_tool_release: Optional workflow tool provenance reference.
    :param level_of_theory: Required level-of-theory reference.
    :param literature_id: Optional literature provenance id.
    """

    type: CalculationType
    quality: CalculationQuality = CalculationQuality.raw

    species_entry_id: int | None = None
    transition_state_entry_id: int | None = None

    software_release: SoftwareReleaseRef
    workflow_tool_release: WorkflowToolReleaseRef | None = None
    level_of_theory: LevelOfTheoryRef

    literature_id: int | None = None
