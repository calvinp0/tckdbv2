"""Tests for the read API endpoints.

Each test class uploads data first, then verifies reads work correctly.
"""

from __future__ import annotations


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
