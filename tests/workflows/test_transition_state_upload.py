"""Tests for the standalone transition-state upload pipeline.

Covers:
- Basic TS upload with primary opt only
- Upload with additional freq/sp calculations + typed result blocks
- Dependency edges and geometry linkage
- Schema validation (type mismatches, disallowed result blocks)
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.app_user import AppUser
from app.db.models.calculation import (
    Calculation,
    CalculationDependency,
    CalculationFreqResult,
    CalculationOptResult,
    CalculationOutputGeometry,
    CalculationSPResult,
)
from app.db.models.common import (
    CalculationDependencyRole,
    CalculationType,
)
from app.db.models.transition_state import TransitionState, TransitionStateEntry
from app.schemas.fragments.calculation import CalculationWithResultsPayload
from app.schemas.workflows.transition_state_upload import (
    TransitionStateUploadRequest,
)
from app.workflows.transition_state import persist_transition_state_upload


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SOFTWARE = {"name": "gaussian", "version": "16", "revision": "C.02"}
_LOT = {"method": "B3LYP", "basis": "6-31G(d)"}
_LOT_SP = {"method": "CCSD(T)", "basis": "cc-pVTZ"}

_XYZ_TS = """\
3
H transfer TS
H  0.0  0.0  0.0
H  0.0  0.0  0.9
H  0.0  0.0  1.8
"""

# Embedded reaction content: [H] + [H][H] → [H] + [H][H]
_REACTION = {
    "reversible": True,
    "reactants": [
        {"species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2}},
        {"species_entry": {"smiles": "[H][H]", "charge": 0, "multiplicity": 1}},
    ],
    "products": [
        {"species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2}},
        {"species_entry": {"smiles": "[H][H]", "charge": 0, "multiplicity": 1}},
    ],
}


def _basic_ts_request() -> TransitionStateUploadRequest:
    """Minimal TS upload request with primary opt only."""
    return TransitionStateUploadRequest(
        reaction=_REACTION,
        charge=0,
        multiplicity=2,
        geometry={"xyz_text": _XYZ_TS},
        primary_opt=CalculationWithResultsPayload(
            type="opt",
            software_release=_SOFTWARE,
            level_of_theory=_LOT,
        ),
        label="H-transfer TS",
        note="test upload",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_basic_ts_upload_creates_concept_and_entry(db_engine) -> None:
    """Primary opt only — verifies TS concept, entry, geometry, and calc."""
    with Session(db_engine) as session, session.begin():
        session.add(AppUser(id=50, username="ts_tester"))
        session.flush()

        ts_entry = persist_transition_state_upload(
            session,
            _basic_ts_request(),
            created_by=50,
        )

        assert ts_entry.id is not None
        assert ts_entry.charge == 0
        assert ts_entry.multiplicity == 2
        assert ts_entry.created_by == 50

        # TS concept
        ts = session.get(TransitionState, ts_entry.transition_state_id)
        assert ts is not None
        assert ts.reaction_entry_id is not None
        assert ts.label == "H-transfer TS"
        assert ts.note == "test upload"

        # Calculation
        calcs = session.scalars(
            select(Calculation).where(
                Calculation.transition_state_entry_id == ts_entry.id
            )
        ).all()
        assert len(calcs) == 1
        assert calcs[0].type == CalculationType.opt

        # Output geometry link
        geo_links = session.scalars(
            select(CalculationOutputGeometry).where(
                CalculationOutputGeometry.calculation_id == calcs[0].id
            )
        ).all()
        assert len(geo_links) == 1


def test_ts_upload_with_additional_calcs_and_results(db_engine) -> None:
    """Upload with freq (+ result) and sp (+ result) additional calcs."""
    with Session(db_engine) as session, session.begin():
        session.add(AppUser(id=51, username="ts_tester_full"))
        session.flush()

        request = TransitionStateUploadRequest(
            reaction=_REACTION,
            charge=0,
            multiplicity=2,
            geometry={"xyz_text": _XYZ_TS},
            primary_opt=CalculationWithResultsPayload(
                type="opt",
                software_release=_SOFTWARE,
                level_of_theory=_LOT,
                opt_result={
                    "converged": True,
                    "n_steps": 42,
                    "final_energy_hartree": -1.234,
                },
            ),
            additional_calculations=[
                CalculationWithResultsPayload(
                    type="freq",
                    software_release=_SOFTWARE,
                    level_of_theory=_LOT,
                    freq_result={
                        "n_imag": 1,
                        "imag_freq_cm1": -1523.4,
                        "zpe_hartree": 0.012,
                    },
                ),
                CalculationWithResultsPayload(
                    type="sp",
                    software_release={"name": "orca", "version": "5.0"},
                    level_of_theory=_LOT_SP,
                    sp_result={"electronic_energy_hartree": -1.567},
                ),
            ],
        )
        ts_entry = persist_transition_state_upload(
            session, request, created_by=51
        )

        # 3 calculations total
        calcs = session.scalars(
            select(Calculation).where(
                Calculation.transition_state_entry_id == ts_entry.id
            )
        ).all()
        assert len(calcs) == 3

        opt_calc = next(c for c in calcs if c.type == CalculationType.opt)
        freq_calc = next(c for c in calcs if c.type == CalculationType.freq)
        sp_calc = next(c for c in calcs if c.type == CalculationType.sp)

        # Opt result
        opt_result = session.get(CalculationOptResult, opt_calc.id)
        assert opt_result is not None
        assert opt_result.converged is True
        assert opt_result.n_steps == 42

        # Freq result
        freq_result = session.get(CalculationFreqResult, freq_calc.id)
        assert freq_result is not None
        assert freq_result.n_imag == 1
        assert freq_result.imag_freq_cm1 == pytest.approx(-1523.4)

        # SP result
        sp_result = session.get(CalculationSPResult, sp_calc.id)
        assert sp_result is not None
        assert sp_result.electronic_energy_hartree == pytest.approx(-1.567)

        # Dependency edges: freq→opt and sp→opt
        deps = session.scalars(
            select(CalculationDependency).where(
                CalculationDependency.parent_calculation_id == opt_calc.id
            )
        ).all()
        assert len(deps) == 2
        dep_roles = {d.dependency_role for d in deps}
        assert CalculationDependencyRole.freq_on in dep_roles
        assert CalculationDependencyRole.single_point_on in dep_roles

        # All 3 calcs share the same geometry
        geo_links = session.scalars(
            select(CalculationOutputGeometry).where(
                CalculationOutputGeometry.calculation_id.in_(
                    [c.id for c in calcs]
                )
            )
        ).all()
        assert len(geo_links) == 3
        geometry_ids = {g.geometry_id for g in geo_links}
        assert len(geometry_ids) == 1  # all point to the same geometry


def test_ts_upload_without_results_succeeds(db_engine) -> None:
    """Additional calcs without result blocks are fine."""
    with Session(db_engine) as session, session.begin():
        session.add(AppUser(id=52, username="ts_no_results"))
        session.flush()

        request = TransitionStateUploadRequest(
            reaction=_REACTION,
            charge=0,
            multiplicity=1,
            geometry={"xyz_text": _XYZ_TS},
            primary_opt=CalculationWithResultsPayload(
                type="opt",
                software_release=_SOFTWARE,
                level_of_theory=_LOT,
            ),
            additional_calculations=[
                CalculationWithResultsPayload(
                    type="freq",
                    software_release=_SOFTWARE,
                    level_of_theory=_LOT,
                ),
            ],
        )
        ts_entry = persist_transition_state_upload(session, request, created_by=52)

        freq_calc = session.scalar(
            select(Calculation).where(
                Calculation.transition_state_entry_id == ts_entry.id,
                Calculation.type == CalculationType.freq,
            )
        )
        assert freq_calc is not None
        # No freq result row
        assert session.get(CalculationFreqResult, freq_calc.id) is None


# ---------------------------------------------------------------------------
# Schema validation tests (no DB needed)
# ---------------------------------------------------------------------------


def test_schema_rejects_non_opt_primary():
    """primary_opt must have type='opt'."""
    with pytest.raises(ValueError, match="primary_opt must have type 'opt'"):
        TransitionStateUploadRequest(
            reaction=_REACTION,
            charge=0,
            multiplicity=1,
            geometry={"xyz_text": "1\n\nH 0 0 0"},
            primary_opt=CalculationWithResultsPayload(
                type="freq",
                software_release=_SOFTWARE,
                level_of_theory=_LOT,
            ),
        )


def test_schema_rejects_opt_in_additional():
    """Additional calculations cannot be type='opt'."""
    with pytest.raises(ValueError, match="not allowed"):
        TransitionStateUploadRequest(
            reaction=_REACTION,
            charge=0,
            multiplicity=1,
            geometry={"xyz_text": "1\n\nH 0 0 0"},
            primary_opt=CalculationWithResultsPayload(
                type="opt",
                software_release=_SOFTWARE,
                level_of_theory=_LOT,
            ),
            additional_calculations=[
                CalculationWithResultsPayload(
                    type="opt",
                    software_release=_SOFTWARE,
                    level_of_theory=_LOT,
                ),
            ],
        )


def test_schema_rejects_mismatched_result_block():
    """freq_result on an sp calculation should fail."""
    with pytest.raises(ValueError, match="not allowed for calculation type"):
        CalculationWithResultsPayload(
            type="sp",
            software_release=_SOFTWARE,
            level_of_theory=_LOT,
            freq_result={"n_imag": 1},
        )


def test_schema_allows_irc_additional():
    """IRC should be accepted as an additional calculation type."""
    request = TransitionStateUploadRequest(
        reaction=_REACTION,
        charge=0,
        multiplicity=1,
        geometry={"xyz_text": "1\n\nH 0 0 0"},
        primary_opt=CalculationWithResultsPayload(
            type="opt",
            software_release=_SOFTWARE,
            level_of_theory=_LOT,
        ),
        additional_calculations=[
            CalculationWithResultsPayload(
                type="irc",
                software_release=_SOFTWARE,
                level_of_theory=_LOT,
            ),
        ],
    )
    assert len(request.additional_calculations) == 1
    assert request.additional_calculations[0].type == CalculationType.irc
