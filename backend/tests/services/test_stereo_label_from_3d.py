"""Unit tests for ``derive_stereo_label_from_3d`` (DR-0018, DR-0031).

This function assigns configurational CIP labels (R/S, E/Z) from 3D geometry.
It was silently dead for months: ``MolFromXYZBlock`` produced a bondless atom
cloud, ``AssignBondOrdersFromTemplate`` then raised ``ValueError: No matching
found``, and a blanket ``except Exception: return None`` swallowed it — so every
input returned ``None`` and every stereoisomer merged into one ``SpeciesEntry``.

These tests pin the repaired behaviour:
- E/Z double bonds and R/S centres are labelled from geometry;
- achiral / no-stereo inputs return ``None``;
- the label string is deterministic under atom re-ordering (canonical rank);
- only *configuration* is labelled — two rotamers of the same configuration
  yield the same label (never a torsional artefact).

Geometries are generated with RDKit ETKDG from a configuration-bearing SMILES,
so the coordinates faithfully encode the intended stereochemistry.
"""

from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import AllChem

from app.chemistry.species import derive_stereo_label_from_3d


def _xyz_from_smiles(smiles: str, *, seed: int = 0xC0FFEE) -> str:
    """Embed a 3D conformer for ``smiles`` and return its XYZ block."""
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    assert AllChem.EmbedMolecule(mol, randomSeed=seed) == 0, smiles
    AllChem.MMFFOptimizeMolecule(mol)
    return Chem.MolToXYZBlock(mol)


# ---------------------------------------------------------------------------
# E/Z double-bond configuration
# ---------------------------------------------------------------------------


class TestEZDoubleBonds:
    def test_cis_diazene_is_Z(self) -> None:
        xyz = _xyz_from_smiles(r"[H]/N=N\[H]")
        assert derive_stereo_label_from_3d("N=N", xyz) == "Z"

    def test_trans_diazene_is_E(self) -> None:
        xyz = _xyz_from_smiles(r"[H]/N=N/[H]")
        assert derive_stereo_label_from_3d("N=N", xyz) == "E"

    def test_cis_2_butene_is_Z(self) -> None:
        xyz = _xyz_from_smiles(r"C/C=C\C")
        assert derive_stereo_label_from_3d("CC=CC", xyz) == "Z"

    def test_trans_2_butene_is_E(self) -> None:
        xyz = _xyz_from_smiles(r"C/C=C/C")
        assert derive_stereo_label_from_3d("CC=CC", xyz) == "E"


# ---------------------------------------------------------------------------
# Tetrahedral chiral-centre configuration
# ---------------------------------------------------------------------------


class TestChiralCentres:
    def test_enantiomers_get_opposite_labels(self) -> None:
        # CHFClBr is the textbook single-stereocentre case. The two hand
        # configurations must produce opposite CIP labels from geometry alone.
        r_like = derive_stereo_label_from_3d(
            "[CH](F)(Cl)Br", _xyz_from_smiles("[C@H](F)(Cl)Br")
        )
        s_like = derive_stereo_label_from_3d(
            "[CH](F)(Cl)Br", _xyz_from_smiles("[C@@H](F)(Cl)Br")
        )
        assert {r_like, s_like} == {"R", "S"}
        assert r_like != s_like


# ---------------------------------------------------------------------------
# Achiral / no-stereo inputs return None
# ---------------------------------------------------------------------------


class TestNoStereoReturnsNone:
    def test_benzene(self) -> None:
        assert derive_stereo_label_from_3d("c1ccccc1", _xyz_from_smiles("c1ccccc1")) is None

    def test_methane(self) -> None:
        assert derive_stereo_label_from_3d("C", _xyz_from_smiles("C")) is None

    def test_hydrazine_n2h4(self) -> None:
        assert derive_stereo_label_from_3d("NN", _xyz_from_smiles("NN")) is None

    def test_dihydrogen(self) -> None:
        assert derive_stereo_label_from_3d("[H][H]", _xyz_from_smiles("[H][H]")) is None

    def test_unparseable_geometry_returns_none(self) -> None:
        assert derive_stereo_label_from_3d("CC=CC", "not an xyz block") is None


# ---------------------------------------------------------------------------
# Determinism: identical label regardless of uploaded atom ordering
# ---------------------------------------------------------------------------


class TestDeterministicOrdering:
    def test_two_stereocentres_order_independent(self) -> None:
        # Same molecule (a 2-stereocentre threonine-like backbone) written with
        # its atoms in two different orders. Without canonical-rank ordering the
        # emitted labels flip ("R,S" vs "S,R") and the species spuriously
        # splits into two entries. They must be identical.
        smi_a = "N[C@@H](O)[C@H](O)C"
        smi_b = "C[C@@H](O)[C@H](O)N"
        label_a = derive_stereo_label_from_3d(smi_a, _xyz_from_smiles(smi_a))
        label_b = derive_stereo_label_from_3d(smi_b, _xyz_from_smiles(smi_b))
        assert label_a is not None and "," in label_a
        assert label_a == label_b


# ---------------------------------------------------------------------------
# Conformer-vs-configuration safety: rotamers must not change the label
# ---------------------------------------------------------------------------


class TestConformerSafety:
    def test_two_rotamers_of_E_2_pentene_both_E(self) -> None:
        # Different torsional conformers of the SAME E configuration. The
        # ethyl/methyl single bonds rotate freely; that torsion must never be
        # mistaken for configurational stereo.
        labels = {
            derive_stereo_label_from_3d("CCC=CC", _xyz_from_smiles(r"CC/C=C/C", seed=seed))
            for seed in (1, 7, 42, 101)
        }
        assert labels == {"E"}
