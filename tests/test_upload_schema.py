import pytest
from pydantic import ValidationError

from app.schemas.workflows.conformer_upload import ConformerUploadRequest


def test_conformer_upload_request_normalizes_nested_identity_fields() -> None:
    request = ConformerUploadRequest(
        species_entry={
            "smiles": " [H] ",
            "charge": 0,
            "multiplicity": 2,
            "stereo_label": "   ",
            "electronic_state_label": "  X  ",
            "term_symbol": "  X2S  ",
        },
        geometry={"xyz_text": " 1\ncomment\nH 0.0 0.0 0.0\n "},
        calculation={
            "type": "sp",
            "software_release": {"name": " Gaussian ", "version": " 16 "},
            "level_of_theory": {"method": " B3LYP ", "basis": " 6-31G(d) "},
        },
        note="  imported  ",
        label="  conf-a  ",
    )

    assert request.species_entry.smiles == "[H]"
    assert request.species_entry.stereo_label is None
    assert request.species_entry.electronic_state_label == "X"
    assert request.species_entry.term_symbol == "X2S"
    assert request.geometry.xyz_text == "1\ncomment\nH 0.0 0.0 0.0"
    assert request.note == "imported"
    assert request.label == "conf-a"


def test_conformer_upload_request_requires_calculation_provenance() -> None:
    with pytest.raises(ValidationError):
        ConformerUploadRequest(
            species_entry={"smiles": "[H]", "charge": 0, "multiplicity": 2},
            geometry={"xyz_text": "1\ncomment\nH 0.0 0.0 0.0"},
            calculation={
                "type": "sp",
                "level_of_theory": {"method": "B3LYP"},
            },
        )
