"""Tests for the read API endpoints.

Each test class uploads data first, then verifies reads work correctly.
"""

from __future__ import annotations

from app.db.models.author import Author
from app.db.models.calculation import CalculationConstraint
from app.db.models.common import ConstraintKind
from app.db.models.energy_correction import (
    EnergyCorrectionScheme,
    FrequencyScaleFactor,
)
from app.db.models.literature import Literature
from app.db.models.literature_author import LiteratureAuthor


# ---------------------------------------------------------------------------
# Test payloads
# ---------------------------------------------------------------------------


def _hydrogen_conformer_payload(label: str = "conf-a") -> dict:
    return {
        "species_entry": {
            "smiles": "[H]",
            "charge": 0,
            "multiplicity": 2,
        },
        "geometry": {
            "xyz_text": "1\nH atom\nH 0.0 0.0 0.0",
        },
        "calculation": {
            "type": "sp",
            "software_release": {"name": "Gaussian", "version": "16"},
            "level_of_theory": {"method": "B3LYP", "basis": "6-31G(d)"},
        },
        "label": label,
    }


def _reaction_payload() -> dict:
    return {
        "reversible": True,
        "reactants": [
            {"species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2}},
        ],
        "products": [
            {"species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2}},
        ],
    }


def _thermo_payload() -> dict:
    return {
        "species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2},
        "scientific_origin": "computed",
        "h298_kj_mol": 217.998,
    }


_XYZ_H2 = "2\nH2\nH 0.0 0.0 0.0\nH 0.0 0.0 0.74"


def _ts_upload_payload() -> dict:
    return {
        "reaction": {
            "reversible": True,
            "reactants": [
                {"species_entry": {"smiles": "[H][H]", "charge": 0, "multiplicity": 1}},
            ],
            "products": [
                {"species_entry": {"smiles": "[H][H]", "charge": 0, "multiplicity": 1}},
            ],
        },
        "charge": 0,
        "multiplicity": 1,
        "geometry": {"xyz_text": _XYZ_H2},
        "primary_opt": {
            "type": "opt",
            "software_release": {"name": "Gaussian", "version": "16"},
            "level_of_theory": {"method": "B3LYP", "basis": "6-31G(d)"},
            "opt_result": {
                "converged": True,
                "n_steps": 10,
                "final_energy_hartree": -1.17,
            },
        },
        "additional_calculations": [
            {
                "type": "freq",
                "software_release": {"name": "Gaussian", "version": "16"},
                "level_of_theory": {"method": "B3LYP", "basis": "6-31G(d)"},
                "freq_result": {
                    "n_imag": 1,
                    "imag_freq_cm1": -1500.0,
                    "zpe_hartree": 0.01,
                },
            },
            {
                "type": "sp",
                "software_release": {"name": "Gaussian", "version": "16"},
                "level_of_theory": {"method": "CCSD(T)", "basis": "cc-pVTZ"},
                "sp_result": {"electronic_energy_hartree": -1.23},
            },
        ],
    }


def _kinetics_payload() -> dict:
    return {
        "reaction": {
            "reversible": True,
            "reactants": [
                {"species_entry": {"smiles": "[H][H]", "charge": 0, "multiplicity": 1}},
                {"species_entry": {"smiles": "[OH]", "charge": 0, "multiplicity": 2}},
            ],
            "products": [
                {"species_entry": {"smiles": "O", "charge": 0, "multiplicity": 1}},
                {"species_entry": {"smiles": "[H]", "charge": 0, "multiplicity": 2}},
            ],
        },
        "scientific_origin": "experimental",
        "a": 2.16e8,
        "a_units": "cm3_mol_s",
        "n": 1.51,
        "reported_ea": 14.35,
        "reported_ea_units": "kj_mol",
    }


# ---------------------------------------------------------------------------
# Species reads
# ---------------------------------------------------------------------------


class TestSpeciesReads:
    def test_list_species_empty(self, client):
        resp = client.get("/api/v1/species")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_species_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/species")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert data["items"][0]["smiles"] == "[H]"

    def test_get_species_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        species_list = client.get("/api/v1/species").json()
        species_id = species_list["items"][0]["id"]

        resp = client.get(f"/api/v1/species/{species_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == species_id

    def test_get_species_not_found(self, client):
        resp = client.get("/api/v1/species/999999")
        assert resp.status_code == 404

    def test_get_species_entry(self, client):
        upload = client.post(
            "/api/v1/uploads/conformers", json=_hydrogen_conformer_payload()
        ).json()
        entry_id = upload["species_entry_id"]

        resp = client.get(f"/api/v1/species-entries/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

    def test_list_conformers_for_entry(self, client):
        upload = client.post(
            "/api/v1/uploads/conformers", json=_hydrogen_conformer_payload()
        ).json()
        entry_id = upload["species_entry_id"]

        resp = client.get(f"/api/v1/species-entries/{entry_id}/conformers")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_list_thermo_for_entry(self, client):
        upload = client.post(
            "/api/v1/uploads/thermo", json=_thermo_payload()
        ).json()
        entry_id = upload["species_entry_id"]

        resp = client.get(f"/api/v1/species-entries/{entry_id}/thermo")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_species_entry_not_found(self, client):
        resp = client.get("/api/v1/species-entries/999999")
        assert resp.status_code == 404

    def test_filter_by_smiles(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/species", params={"smiles": "[H]"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_filter_by_smiles_no_match(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/species", params={"smiles": "[He]"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_charge_and_multiplicity(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get(
            "/api/v1/species", params={"charge": 0, "multiplicity": 2}
        )
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Reaction reads
# ---------------------------------------------------------------------------


class TestReactionReads:
    def test_list_reactions_empty(self, client):
        resp = client.get("/api/v1/reactions")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_reactions_after_upload(self, client):
        client.post("/api/v1/uploads/reactions", json=_reaction_payload())
        resp = client.get("/api/v1/reactions")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_reaction_entry(self, client):
        upload = client.post(
            "/api/v1/uploads/reactions", json=_reaction_payload()
        ).json()
        entry_id = upload["id"]

        resp = client.get(f"/api/v1/reaction-entries/{entry_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

    def test_reaction_entry_not_found(self, client):
        resp = client.get("/api/v1/reaction-entries/999999")
        assert resp.status_code == 404

    def test_filter_by_reversible(self, client):
        client.post("/api/v1/uploads/reactions", json=_reaction_payload())
        resp = client.get("/api/v1/reactions", params={"reversible": True})
        assert resp.json()["total"] >= 1

    def test_filter_by_reversible_no_match(self, client):
        client.post("/api/v1/uploads/reactions", json=_reaction_payload())
        resp = client.get("/api/v1/reactions", params={"reversible": False})
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Kinetics reads
# ---------------------------------------------------------------------------


class TestKineticsReads:
    def test_list_kinetics_empty(self, client):
        resp = client.get("/api/v1/kinetics")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_kinetics_not_found(self, client):
        resp = client.get("/api/v1/kinetics/999999")
        assert resp.status_code == 404

    def test_list_kinetics_after_upload(self, client):
        upload = client.post(
            "/api/v1/uploads/kinetics", json=_kinetics_payload()
        )
        assert upload.status_code == 201
        resp = client.get("/api/v1/kinetics")
        assert resp.json()["total"] >= 1

    def test_filter_by_scientific_origin(self, client):
        client.post("/api/v1/uploads/kinetics", json=_kinetics_payload())
        resp = client.get(
            "/api/v1/kinetics", params={"scientific_origin": "experimental"}
        )
        assert resp.json()["total"] >= 1

    def test_filter_by_scientific_origin_no_match(self, client):
        client.post("/api/v1/uploads/kinetics", json=_kinetics_payload())
        resp = client.get(
            "/api/v1/kinetics", params={"scientific_origin": "computed"}
        )
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Thermo reads
# ---------------------------------------------------------------------------


class TestThermoReads:
    def test_list_thermo_empty(self, client):
        resp = client.get("/api/v1/thermo")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_get_thermo_after_upload(self, client):
        upload = client.post(
            "/api/v1/uploads/thermo", json=_thermo_payload()
        ).json()
        thermo_id = upload["id"]

        resp = client.get(f"/api/v1/thermo/{thermo_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == thermo_id

    def test_thermo_not_found(self, client):
        resp = client.get("/api/v1/thermo/999999")
        assert resp.status_code == 404

    def test_filter_by_scientific_origin(self, client):
        client.post("/api/v1/uploads/thermo", json=_thermo_payload())
        resp = client.get(
            "/api/v1/thermo", params={"scientific_origin": "computed"}
        )
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Transition state reads
# ---------------------------------------------------------------------------


class TestTransitionStateReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/transition-states")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post(
            "/api/v1/uploads/transition-states", json=_ts_upload_payload()
        )
        resp = client.get("/api/v1/transition-states")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        upload = client.post(
            "/api/v1/uploads/transition-states", json=_ts_upload_payload()
        ).json()
        ts_id = upload["transition_state_id"]
        resp = client.get(f"/api/v1/transition-states/{ts_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == ts_id

    def test_not_found(self, client):
        resp = client.get("/api/v1/transition-states/999999")
        assert resp.status_code == 404

    def test_filter_by_reaction_entry_id(self, client):
        upload = client.post(
            "/api/v1/uploads/transition-states", json=_ts_upload_payload()
        ).json()
        resp = client.get(
            "/api/v1/transition-states",
            params={"reaction_entry_id": upload["reaction_entry_id"]},
        )
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Calculation reads
# ---------------------------------------------------------------------------


class TestCalculationReads:
    """Tests using TS upload which creates opt+freq+sp calculations with
    dependencies and geometry links."""

    def _upload_ts(self, client):
        return client.post(
            "/api/v1/uploads/transition-states", json=_ts_upload_payload()
        ).json()

    def test_list_empty(self, client):
        resp = client.get("/api/v1/calculations")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        self._upload_ts(client)
        resp = client.get("/api/v1/calculations")
        assert resp.json()["total"] >= 3  # opt + freq + sp

    def test_get_by_id(self, client):
        self._upload_ts(client)
        calcs = client.get("/api/v1/calculations").json()["items"]
        calc_id = calcs[0]["id"]
        resp = client.get(f"/api/v1/calculations/{calc_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == calc_id
        assert "created_by" not in resp.json()  # policy: no uploader identity

    def test_not_found(self, client):
        resp = client.get("/api/v1/calculations/999999")
        assert resp.status_code == 404

    def test_filter_by_type(self, client):
        self._upload_ts(client)
        resp = client.get("/api/v1/calculations", params={"type": "opt"})
        assert resp.json()["total"] >= 1
        assert all(c["type"] == "opt" for c in resp.json()["items"])

    def test_filter_by_type_no_match(self, client):
        self._upload_ts(client)
        resp = client.get("/api/v1/calculations", params={"type": "scan"})
        assert resp.json()["total"] == 0

    def test_joined_filter_by_method(self, client):
        self._upload_ts(client)
        resp = client.get("/api/v1/calculations", params={"method": "B3LYP"})
        # opt + freq use B3LYP; sp uses CCSD(T)
        assert resp.json()["total"] >= 2

    def test_joined_filter_by_method_no_match(self, client):
        self._upload_ts(client)
        resp = client.get("/api/v1/calculations", params={"method": "MP2"})
        assert resp.json()["total"] == 0

    # -- SP / opt / freq results (1:1 → 404 when absent) --

    def test_opt_result_present(self, client):
        self._upload_ts(client)
        opt_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "opt"
        )
        resp = client.get(f"/api/v1/calculations/{opt_calc['id']}/opt-result")
        assert resp.status_code == 200
        assert resp.json()["converged"] is True

    def test_freq_result_present(self, client):
        self._upload_ts(client)
        freq_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "freq"
        )
        resp = client.get(f"/api/v1/calculations/{freq_calc['id']}/freq-result")
        assert resp.status_code == 200
        assert resp.json()["n_imag"] == 1

    def test_sp_result_present(self, client):
        self._upload_ts(client)
        sp_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "sp"
        )
        resp = client.get(f"/api/v1/calculations/{sp_calc['id']}/sp-result")
        assert resp.status_code == 200
        assert resp.json()["electronic_energy_hartree"] is not None

    def test_result_missing_returns_404(self, client):
        self._upload_ts(client)
        # opt calc has no freq result
        opt_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "opt"
        )
        resp = client.get(f"/api/v1/calculations/{opt_calc['id']}/freq-result")
        assert resp.status_code == 404

    def test_result_parent_missing_returns_404(self, client):
        resp = client.get("/api/v1/calculations/999999/sp-result")
        assert resp.status_code == 404

    # -- Input/output geometries (1:N → [] when empty) --

    def test_output_geometries_with_embedded_payload(self, client):
        self._upload_ts(client)
        opt_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "opt"
        )
        resp = client.get(
            f"/api/v1/calculations/{opt_calc['id']}/output-geometries"
        )
        assert resp.status_code == 200
        geoms = resp.json()
        assert len(geoms) >= 1
        # Verify embedded geometry payload
        assert "geometry" in geoms[0]
        assert "natoms" in geoms[0]["geometry"]
        assert geoms[0]["output_order"] >= 1

    def test_input_geometries_ordered(self, client):
        self._upload_ts(client)
        opt_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "opt"
        )
        resp = client.get(
            f"/api/v1/calculations/{opt_calc['id']}/input-geometries"
        )
        assert resp.status_code == 200
        geoms = resp.json()
        orders = [g["input_order"] for g in geoms]
        assert orders == sorted(orders)

    # -- Dependencies (1:N → [] when empty) --

    def test_dependencies_present(self, client):
        self._upload_ts(client)
        # freq and sp calculations depend on the opt calculation
        freq_calc = next(
            c for c in client.get("/api/v1/calculations").json()["items"]
            if c["type"] == "freq"
        )
        resp = client.get(
            f"/api/v1/calculations/{freq_calc['id']}/dependencies"
        )
        assert resp.status_code == 200, resp.json()
        deps = resp.json()
        assert len(deps) >= 1
        # Verify direction field is present
        assert all("direction" in d for d in deps)

    def test_dependencies_empty_when_none(self, client):
        # Upload a simple conformer (sp calc with no deps)
        client.post(
            "/api/v1/uploads/conformers", json=_hydrogen_conformer_payload()
        )
        calcs = client.get("/api/v1/calculations").json()["items"]
        sp_calc = next(c for c in calcs if c["type"] == "sp")
        resp = client.get(
            f"/api/v1/calculations/{sp_calc['id']}/dependencies"
        )
        assert resp.status_code == 200
        assert resp.json() == []

    # -- Constraints (1:N → [] when empty) --

    def test_constraints_empty_when_none(self, client):
        self._upload_ts(client)
        calcs = client.get("/api/v1/calculations").json()["items"]
        resp = client.get(
            f"/api/v1/calculations/{calcs[0]['id']}/constraints"
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_constraints_with_data(self, client, db_session):
        self._upload_ts(client)
        calc_id = client.get("/api/v1/calculations").json()["items"][0]["id"]

        # Insert a constraint via raw ORM (no upload creates these)
        db_session.add(
            CalculationConstraint(
                calculation_id=calc_id,
                constraint_index=1,
                constraint_kind=ConstraintKind.bond,
                atom1_index=1,
                atom2_index=2,
                target_value=0.74,
            )
        )
        db_session.flush()

        resp = client.get(f"/api/v1/calculations/{calc_id}/constraints")
        assert resp.status_code == 200
        constraints = resp.json()
        assert len(constraints) == 1
        assert constraints[0]["constraint_index"] == 1
        assert constraints[0]["constraint_kind"] == "bond"


# ---------------------------------------------------------------------------
# Geometry reads
# ---------------------------------------------------------------------------


class TestGeometryReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/geometries")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/geometries")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        geom = client.get("/api/v1/geometries").json()["items"][0]
        resp = client.get(f"/api/v1/geometries/{geom['id']}")
        assert resp.status_code == 200
        assert resp.json()["natoms"] == 1

    def test_not_found(self, client):
        resp = client.get("/api/v1/geometries/999999")
        assert resp.status_code == 404

    def test_filter_by_natoms(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/geometries", params={"natoms": 1})
        assert resp.json()["total"] >= 1

    def test_filter_by_natoms_no_match(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/geometries", params={"natoms": 100})
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Level of theory reads
# ---------------------------------------------------------------------------


class TestLevelOfTheoryReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/levels-of-theory")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/levels-of-theory")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        lot = client.get("/api/v1/levels-of-theory").json()["items"][0]
        resp = client.get(f"/api/v1/levels-of-theory/{lot['id']}")
        assert resp.status_code == 200
        assert resp.json()["method"] == "B3LYP"

    def test_not_found(self, client):
        resp = client.get("/api/v1/levels-of-theory/999999")
        assert resp.status_code == 404

    def test_filter_by_method(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/levels-of-theory", params={"method": "B3LYP"})
        assert resp.json()["total"] >= 1

    def test_filter_by_method_no_match(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/levels-of-theory", params={"method": "MP2"})
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Software reads
# ---------------------------------------------------------------------------


class TestSoftwareReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/software")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/software")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        sw = client.get("/api/v1/software").json()["items"][0]
        resp = client.get(f"/api/v1/software/{sw['id']}")
        assert resp.status_code == 200

    def test_not_found(self, client):
        resp = client.get("/api/v1/software/999999")
        assert resp.status_code == 404

    def test_filter_by_name(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/software", params={"name": "Gaussian"})
        assert resp.json()["total"] >= 1


class TestSoftwareReleaseReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/software-releases")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/software-releases")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        release = client.get("/api/v1/software-releases").json()["items"][0]
        resp = client.get(f"/api/v1/software-releases/{release['id']}")
        assert resp.status_code == 200

    def test_not_found(self, client):
        resp = client.get("/api/v1/software-releases/999999")
        assert resp.status_code == 404

    def test_filter_by_version(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/software-releases", params={"version": "16"})
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Literature reads (seeded via raw ORM insert — uploads don't expose authors)
# ---------------------------------------------------------------------------


class TestLiteratureReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/literature")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_and_get_with_authors(self, client, db_session):
        author = Author(given_name="Jane", family_name="Doe", full_name="Jane Doe")
        db_session.add(author)
        db_session.flush()

        lit = Literature(
            kind="article",
            title="Test Paper",
            year=2024,
            journal="J. Test",
            doi="10.1234/test.2024",
        )
        db_session.add(lit)
        db_session.flush()
        db_session.add(
            LiteratureAuthor(
                literature_id=lit.id,
                author_id=author.id,
                author_order=1,
            )
        )
        db_session.flush()
        lit_id = lit.id

        resp = client.get("/api/v1/literature")
        assert resp.json()["total"] >= 1

        resp = client.get(f"/api/v1/literature/{lit_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Paper"
        assert len(data["authors"]) == 1
        assert data["authors"][0]["author_order"] == 1

    def test_not_found(self, client):
        resp = client.get("/api/v1/literature/999999")
        assert resp.status_code == 404

    def test_filter_by_doi(self, client, db_session):
        db_session.add(
            Literature(
                kind="article",
                title="DOI Paper",
                doi="10.5555/test.doi",
            )
        )
        db_session.flush()
        resp = client.get("/api/v1/literature", params={"doi": "10.5555/test.doi"})
        assert resp.json()["total"] >= 1

    def test_filter_by_doi_no_match(self, client, db_session):
        db_session.add(
            Literature(
                kind="article",
                title="DOI Paper",
                doi="10.5555/test.doi",
            )
        )
        db_session.flush()
        resp = client.get("/api/v1/literature", params={"doi": "10.9999/no.match"})
        assert resp.json()["total"] == 0


# ---------------------------------------------------------------------------
# Conformer reads
# ---------------------------------------------------------------------------


class TestConformerGroupReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/conformer-groups")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/conformer-groups")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        group = client.get("/api/v1/conformer-groups").json()["items"][0]
        resp = client.get(f"/api/v1/conformer-groups/{group['id']}")
        assert resp.status_code == 200

    def test_not_found(self, client):
        resp = client.get("/api/v1/conformer-groups/999999")
        assert resp.status_code == 404


class TestConformerObservationReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/conformer-observations")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        resp = client.get("/api/v1/conformer-observations")
        assert resp.json()["total"] >= 1

    def test_get_by_id(self, client):
        upload = client.post(
            "/api/v1/uploads/conformers", json=_hydrogen_conformer_payload()
        ).json()
        resp = client.get(f"/api/v1/conformer-observations/{upload['id']}")
        assert resp.status_code == 200

    def test_not_found(self, client):
        resp = client.get("/api/v1/conformer-observations/999999")
        assert resp.status_code == 404

    def test_filter_by_conformer_group_id(self, client):
        upload = client.post(
            "/api/v1/uploads/conformers", json=_hydrogen_conformer_payload()
        ).json()
        resp = client.get(
            "/api/v1/conformer-observations",
            params={"conformer_group_id": upload["conformer_group_id"]},
        )
        assert resp.json()["total"] >= 1


# ---------------------------------------------------------------------------
# Energy correction reads (seeded via raw ORM insert — reference layer)
# ---------------------------------------------------------------------------


class TestEnergyCorrectionSchemeReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/energy-correction-schemes")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_and_get(self, client, db_session):
        scheme = EnergyCorrectionScheme(
            kind="bac_petersson",
            name="Test BAC Scheme",
        )
        db_session.add(scheme)
        db_session.flush()
        scheme_id = scheme.id

        resp = client.get("/api/v1/energy-correction-schemes")
        assert resp.json()["total"] >= 1

        resp = client.get(f"/api/v1/energy-correction-schemes/{scheme_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test BAC Scheme"

    def test_not_found(self, client):
        resp = client.get("/api/v1/energy-correction-schemes/999999")
        assert resp.status_code == 404


class TestFrequencyScaleFactorReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/frequency-scale-factors")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_and_get(self, client, db_session):
        # Need an LOT row first (created by conformer upload)
        client.post("/api/v1/uploads/conformers", json=_hydrogen_conformer_payload())
        lot = client.get("/api/v1/levels-of-theory").json()["items"][0]

        fsf = FrequencyScaleFactor(
            level_of_theory_id=lot["id"],
            scale_kind="fundamental",
            value=0.967,
        )
        db_session.add(fsf)
        db_session.flush()
        fsf_id = fsf.id

        resp = client.get("/api/v1/frequency-scale-factors")
        assert resp.json()["total"] >= 1

        resp = client.get(f"/api/v1/frequency-scale-factors/{fsf_id}")
        assert resp.status_code == 200
        assert resp.json()["value"] == 0.967

    def test_not_found(self, client):
        resp = client.get("/api/v1/frequency-scale-factors/999999")
        assert resp.status_code == 404


class TestAppliedEnergyCorrectionReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/applied-energy-corrections")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_not_found(self, client):
        resp = client.get("/api/v1/applied-energy-corrections/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Statmech reads
# ---------------------------------------------------------------------------


class TestStatmechReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/statmech")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_not_found(self, client):
        resp = client.get("/api/v1/statmech/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Transport reads
# ---------------------------------------------------------------------------


class TestTransportReads:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/transport")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_not_found(self, client):
        resp = client.get("/api/v1/transport/999999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestPagination:
    def test_species_pagination_params(self, client):
        resp = client.get("/api/v1/species?skip=0&limit=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["skip"] == 0
        assert data["limit"] == 10

    def test_invalid_limit(self, client):
        resp = client.get("/api/v1/species?limit=999")
        assert resp.status_code == 422
