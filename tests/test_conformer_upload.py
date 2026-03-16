from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.calculation import Calculation, CalculationOutputGeometry
from app.db.models.geometry import Geometry
from app.db.models.species import ConformerGroup, ConformerObservation, Species, SpeciesEntry
from app.schemas.workflows.conformer_upload import ConformerUploadRequest
from app.services.conformer_upload import persist_conformer_upload


def _hydrogen_request(*, label: str | None = None) -> ConformerUploadRequest:
    return ConformerUploadRequest(
        species_entry={
            "smiles": "[H]",
            "charge": 0,
            "multiplicity": 2,
        },
        geometry={
            "xyz_text": "1\nH atom\nH 0.0 0.0 0.0",
        },
        calculation={
            "type": "sp",
            "software_release": {"name": "Gaussian", "version": "16"},
            "level_of_theory": {"method": "B3LYP", "basis": "6-31G(d)"},
        },
        label=label,
        note="uploaded conformer",
    )


def test_persist_conformer_upload_creates_expected_rows(db_engine) -> None:
    with Session(db_engine) as session:
        with session.begin():
            observation = persist_conformer_upload(session, _hydrogen_request(label="conf-a"))

            stored_observation = session.scalar(
                select(ConformerObservation).where(
                    ConformerObservation.id == observation.id
                )
            )
            assert stored_observation is not None

            calculation = session.scalar(
                select(Calculation).where(Calculation.id == observation.calculation_id)
            )
            assert calculation is not None
            assert calculation.species_entry_id is not None

            geometry_link = session.scalar(
                select(CalculationOutputGeometry).where(
                    CalculationOutputGeometry.calculation_id == calculation.id
                )
            )
            assert geometry_link is not None

            geometry = session.scalar(
                select(Geometry).where(Geometry.id == geometry_link.geometry_id)
            )
            assert geometry is not None
            assert geometry.natoms == 1

            conformer_group = session.scalar(
                select(ConformerGroup).where(
                    ConformerGroup.id == observation.conformer_group_id
                )
            )
            assert conformer_group is not None
            assert conformer_group.label == "conf-a"

            assert session.scalar(select(Species)) is not None
            assert session.scalar(select(SpeciesEntry)) is not None


def test_persist_conformer_upload_reuses_species_entry_and_labeled_group(db_engine) -> None:
    with Session(db_engine) as session:
        with session.begin():
            first = persist_conformer_upload(session, _hydrogen_request(label="conf-a"))
            second = persist_conformer_upload(session, _hydrogen_request(label="conf-a"))

            first_group = session.scalar(
                select(ConformerGroup).where(ConformerGroup.id == first.conformer_group_id)
            )
            second_group = session.scalar(
                select(ConformerGroup).where(ConformerGroup.id == second.conformer_group_id)
            )
            first_calc = session.scalar(
                select(Calculation).where(Calculation.id == first.calculation_id)
            )
            second_calc = session.scalar(
                select(Calculation).where(Calculation.id == second.calculation_id)
            )

            assert first_group is not None
            assert second_group is not None
            assert first_group.id == second_group.id

            assert first_calc is not None
            assert second_calc is not None
            assert first_calc.id != second_calc.id
            assert first_calc.species_entry_id == second_calc.species_entry_id
