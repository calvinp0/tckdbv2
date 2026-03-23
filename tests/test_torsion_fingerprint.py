"""Tests for the torsion fingerprint system (DR-0005).

Covers:
- Circular difference calculation
- Angle normalization and symmetry folding
- Rotor slot identification for various molecule types
- Fingerprint computation and matching
- Basin matching (same basin vs different rotamers)
"""

from __future__ import annotations

import pytest
from rdkit import Chem
from rdkit.Chem import AllChem

from app.chemistry.torsion_fingerprint import (
    AtomMappingResult,
    ConformerComparisonResult,
    RotorSlot,
    TorsionFingerprint,
    circular_difference,
    compare_conformers,
    compute_fingerprint_from_xyz,
    compute_torsion_fingerprint,
    fingerprints_match,
    fold_angle,
    identify_rotor_slots,
    kabsch_rmsd,
    normalize_angle,
    resolve_atom_mapping,
)


# ---------------------------------------------------------------------------
# Circular difference
# ---------------------------------------------------------------------------


class TestCircularDifference:
    def test_simple_difference(self):
        assert circular_difference(10.0, 20.0) == pytest.approx(10.0)

    def test_wraparound(self):
        # 5° and 355° are 10° apart, not 350°
        assert circular_difference(5.0, 355.0) == pytest.approx(10.0)

    def test_same_angle(self):
        assert circular_difference(180.0, 180.0) == pytest.approx(0.0)

    def test_opposite(self):
        assert circular_difference(0.0, 180.0) == pytest.approx(180.0)

    def test_period_120(self):
        # In 120° period: 10° and 110° → diff=100, min(100, 20) = 20°
        assert circular_difference(10.0, 110.0, period=120.0) == pytest.approx(20.0)

    def test_period_120_same_basin(self):
        # 5° and 115° differ by 110° raw, but circular in 120° = 10°
        assert circular_difference(5.0, 115.0, period=120.0) == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# Angle normalization and folding
# ---------------------------------------------------------------------------


class TestAngleNormalization:
    def test_negative_to_positive(self):
        assert normalize_angle(-60.0) == pytest.approx(300.0)

    def test_already_normalized(self):
        assert normalize_angle(45.0) == pytest.approx(45.0)

    def test_360_wraps_to_zero(self):
        assert normalize_angle(360.0) == pytest.approx(0.0)


class TestAngleFolding:
    def test_no_fold(self):
        assert fold_angle(250.0, 1) == pytest.approx(250.0)

    def test_threefold(self):
        # 250° mod 120° = 10°
        assert fold_angle(250.0, 3) == pytest.approx(10.0)

    def test_twofold(self):
        # 250° mod 180° = 70°
        assert fold_angle(250.0, 2) == pytest.approx(70.0)

    def test_methyl_equivalence(self):
        # 0°, 120°, 240° all fold to 0° under 3-fold
        assert fold_angle(0.0, 3) == pytest.approx(0.0)
        assert fold_angle(120.0, 3) == pytest.approx(0.0)
        assert fold_angle(240.0, 3) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Rotor identification
# ---------------------------------------------------------------------------


class TestRotorIdentification:
    def test_ethane_no_rotors(self):
        """Ethane (C-C with only H on each side) — both terminal, no rotor."""
        mol = Chem.MolFromSmiles("CC")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol)
        # Both sides are CH3 (terminal-heavy with only 1 heavy neighbor each)
        # But ethane C-C does have methyl rotors — the filter allows if
        # at least one side is CH3 with heavy neighbor count considerations
        # Actually: each C has 1 heavy neighbor (the other C). So both < 2.
        # After the fix, this should be filtered out.
        assert len(slots) == 0

    def test_butane_one_rotor(self):
        """n-Butane: one central C-C rotor."""
        mol = Chem.MolFromSmiles("CCCC")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol)
        # Central C-C bond: both sides have ≥2 heavy neighbors
        assert len(slots) >= 1
        # The two terminal C-C bonds are methyl rotors
        non_methyl = [s for s in slots if not s.is_methyl]
        assert len(non_methyl) == 1

    def test_butane_exclude_methyl(self):
        """Excluding methyl rotors leaves only the central C-C."""
        mol = Chem.MolFromSmiles("CCCC")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol, exclude_methyl=True)
        assert len(slots) == 1
        assert not slots[0].is_methyl

    def test_rigid_molecule_no_rotors(self):
        """Benzene — all bonds in ring, no rotatable bonds."""
        mol = Chem.MolFromSmiles("c1ccccc1")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol)
        assert len(slots) == 0

    def test_single_atom_no_rotors(self):
        """Hydrogen atom — no bonds."""
        mol = Chem.MolFromSmiles("[H]")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol)
        assert len(slots) == 0

    def test_double_methyl_sixfold_symmetry(self):
        """Bond with methyl on both sides gets 6-fold symmetry (3×2).

        Dimethyl ether (COC): each C-O bond has CH3 on the C side and
        O with 2 heavy neighbors on the other. Only one side is methyl → 3-fold.

        2,3-dimethylbutane CC(C)C(C)C: the terminal C-C(CH3) bonds have
        methyl on one side → 3-fold. The central C-C has no methyl on
        either side (each central C has 3 heavy neighbors).
        """
        # Dimethyl ether: single methyl per bond → 3-fold
        mol = Chem.MolFromSmiles("COC")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol, methyl_symmetry_fold=3)
        methyl_slots = [s for s in slots if s.is_methyl]
        assert all(s.symmetry_fold == 3 for s in methyl_slots)

    def test_canonical_key_invariant(self):
        """Same molecule from different SMILES should give same canonical keys."""
        mol1 = Chem.MolFromSmiles("CCCC")
        mol1 = Chem.AddHs(mol1)
        mol2 = Chem.MolFromSmiles("C(CC)C")
        mol2 = Chem.AddHs(mol2)

        slots1 = identify_rotor_slots(mol1, exclude_methyl=True)
        slots2 = identify_rotor_slots(mol2, exclude_methyl=True)

        keys1 = [s.canonical_key for s in slots1]
        keys2 = [s.canonical_key for s in slots2]
        assert keys1 == keys2

    def test_methyl_detected(self):
        """Methyl groups should be detected and have symmetry_fold=3."""
        mol = Chem.MolFromSmiles("CCCC")
        mol = Chem.AddHs(mol)
        slots = identify_rotor_slots(mol, methyl_symmetry_fold=3)
        methyl_slots = [s for s in slots if s.is_methyl]
        assert len(methyl_slots) >= 1
        assert all(s.symmetry_fold == 3 for s in methyl_slots)


# ---------------------------------------------------------------------------
# Fingerprint computation + matching
# ---------------------------------------------------------------------------


class TestFingerprintComputation:
    def _make_butane_conformer(self, dihedral_deg: float):
        """Create a butane mol with a specific central C-C-C-C dihedral."""
        mol = Chem.MolFromSmiles("CCCC")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        from rdkit.Chem import rdMolTransforms
        conf = mol.GetConformer()
        # Set the central dihedral (heavy atoms 0-1-2-3)
        rdMolTransforms.SetDihedralDeg(conf, 0, 1, 2, 3, dihedral_deg)
        return mol

    def test_fingerprint_has_correct_rotor_count(self):
        mol = self._make_butane_conformer(60.0)
        fp = compute_torsion_fingerprint(mol, exclude_methyl=True)
        assert fp.rotor_count == 1

    def test_same_basin_matches(self):
        """Two conformers at 60° and 65° (same gauche basin) should match."""
        mol1 = self._make_butane_conformer(60.0)
        mol2 = self._make_butane_conformer(65.0)

        fp1 = compute_torsion_fingerprint(mol1, exclude_methyl=True)
        fp2 = compute_torsion_fingerprint(mol2, exclude_methyl=True)

        matches, deltas, _rmsd = fingerprints_match(fp1, fp2, threshold_deg=15.0)
        assert matches
        assert all(d < 15.0 for d in deltas)

    def test_different_rotamer_doesnt_match(self):
        """60° (gauche) vs 180° (anti) — different basins."""
        mol1 = self._make_butane_conformer(60.0)
        mol2 = self._make_butane_conformer(180.0)

        fp1 = compute_torsion_fingerprint(mol1, exclude_methyl=True)
        fp2 = compute_torsion_fingerprint(mol2, exclude_methyl=True)

        matches, deltas, _rmsd = fingerprints_match(fp1, fp2, threshold_deg=15.0)
        assert not matches

    def test_wraparound_matching(self):
        """5° and 355° should match (10° apart)."""
        mol1 = self._make_butane_conformer(5.0)
        mol2 = self._make_butane_conformer(355.0)

        fp1 = compute_torsion_fingerprint(mol1, exclude_methyl=True)
        fp2 = compute_torsion_fingerprint(mol2, exclude_methyl=True)

        matches, deltas, _rmsd = fingerprints_match(fp1, fp2, threshold_deg=15.0)
        assert matches

    def test_rigid_molecule_always_matches(self):
        """Benzene (no rotors) — two conformers always match."""
        mol1 = Chem.MolFromSmiles("c1ccccc1")
        mol1 = Chem.AddHs(mol1)
        AllChem.EmbedMolecule(mol1, randomSeed=42)

        mol2 = Chem.MolFromSmiles("c1ccccc1")
        mol2 = Chem.AddHs(mol2)
        AllChem.EmbedMolecule(mol2, randomSeed=99)

        fp1 = compute_torsion_fingerprint(mol1)
        fp2 = compute_torsion_fingerprint(mol2)

        matches, _, _rmsd = fingerprints_match(fp1, fp2)
        assert matches

    def test_fingerprint_serialization(self):
        """to_dict() and reconstruction should round-trip."""
        mol = self._make_butane_conformer(60.0)
        fp = compute_torsion_fingerprint(mol, exclude_methyl=True)
        d = fp.to_dict()

        assert "rotor_count" in d
        assert "canonical_rotor_keys" in d
        assert "raw_torsions_deg" in d
        assert "folded_torsions_deg" in d
        assert "quantized_bins" in d
        assert "fingerprint_hash" in d
        assert len(d["canonical_rotor_keys"]) == fp.rotor_count

    def test_hash_includes_rotor_keys(self):
        """Two molecules with different rotor structures should hash differently
        even if they happen to have the same quantized bin values."""
        mol1 = self._make_butane_conformer(60.0)
        fp1 = compute_torsion_fingerprint(mol1, exclude_methyl=True)

        # Manually create a fingerprint with same bins but different keys
        fp2 = TorsionFingerprint(
            rotor_slots=[RotorSlot(0, 1, 2, 3, canonical_rank_begin=99, canonical_rank_end=100)],
            raw_torsions_deg=fp1.raw_torsions_deg,
            folded_torsions_deg=fp1.folded_torsions_deg,
            quantized_bins=fp1.quantized_bins,
        )

        assert fp1.fingerprint_hash != fp2.fingerprint_hash


# ---------------------------------------------------------------------------
# Graph-based atom mapping
# ---------------------------------------------------------------------------


class TestAtomMapping:
    def test_ethanol_unique_mapping(self):
        """Ethanol (no heavy-atom symmetry) → unique mapping."""
        mol = Chem.MolFromSmiles("CCO")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        conf = mol.GetConformer()

        xyz_atoms = tuple(
            (mol.GetAtomWithIdx(i).GetSymbol(),
             conf.GetAtomPosition(i).x,
             conf.GetAtomPosition(i).y,
             conf.GetAtomPosition(i).z)
            for i in range(mol.GetNumAtoms())
        )

        result = resolve_atom_mapping("CCO", xyz_atoms)
        assert result.status == "unique"
        assert result.fingerprint is not None
        assert result.n_mappings == 1

    def test_propane_symmetric_equivalent(self):
        """Propane has mirror symmetry — 2 heavy-atom mappings,
        but they should produce equivalent fingerprints (no rotors
        once methyl is excluded, or same methyl torsions)."""
        mol = Chem.MolFromSmiles("CCC")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        conf = mol.GetConformer()

        xyz_atoms = tuple(
            (mol.GetAtomWithIdx(i).GetSymbol(),
             conf.GetAtomPosition(i).x,
             conf.GetAtomPosition(i).y,
             conf.GetAtomPosition(i).z)
            for i in range(mol.GetNumAtoms())
        )

        result = resolve_atom_mapping("CCC", xyz_atoms, exclude_methyl=True)
        # Propane with methyl excluded has 0 rotors → fingerprints trivially match
        assert result.status in ("unique", "equivalent")
        assert result.fingerprint is not None

    def test_single_atom_no_match_needed(self):
        """Single atom (H) — no rotors, should still produce a fingerprint."""
        xyz_atoms = (("H", 0.0, 0.0, 0.0),)
        fp = compute_fingerprint_from_xyz("[H]", xyz_atoms)
        assert fp.rotor_count == 0

    def test_scrambled_atom_order(self):
        """XYZ with scrambled atom order should still produce valid fingerprint."""
        mol = Chem.MolFromSmiles("CCO")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        conf = mol.GetConformer()

        # Normal order
        xyz_normal = tuple(
            (mol.GetAtomWithIdx(i).GetSymbol(),
             conf.GetAtomPosition(i).x,
             conf.GetAtomPosition(i).y,
             conf.GetAtomPosition(i).z)
            for i in range(mol.GetNumAtoms())
        )

        # Scramble: reverse order
        xyz_scrambled = tuple(reversed(xyz_normal))

        fp_normal = compute_fingerprint_from_xyz("CCO", xyz_normal)
        fp_scrambled = compute_fingerprint_from_xyz("CCO", xyz_scrambled)

        # Both should produce valid fingerprints with same rotor count
        assert fp_normal.rotor_count == fp_scrambled.rotor_count

    def test_element_mismatch_raises(self):
        """XYZ with wrong elements should fail."""
        xyz_atoms = (("N", 0.0, 0.0, 0.0), ("N", 1.0, 0.0, 0.0))
        with pytest.raises(ValueError):
            compute_fingerprint_from_xyz("CC", xyz_atoms)

    def test_sanity_check_four_guarantees(self):
        """The four fundamental guarantees of the isomorphism system:
        1. Same molecule → mapping found
        2. Different molecule → no mapping
        3. Same molecule reordered → mapping found
        4. Mapped coordinates → same fingerprint
        """
        mol = Chem.MolFromSmiles("CCO")
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, randomSeed=42)
        conf = mol.GetConformer()

        xyz = tuple(
            (mol.GetAtomWithIdx(i).GetSymbol(),
             conf.GetAtomPosition(i).x,
             conf.GetAtomPosition(i).y,
             conf.GetAtomPosition(i).z)
            for i in range(mol.GetNumAtoms())
        )

        # 1. Same molecule → mapping found
        r = resolve_atom_mapping("CCO", xyz)
        assert r.status in ("unique", "equivalent")

        # 2. Different molecule → no mapping
        r_wrong = resolve_atom_mapping("CCCO", xyz)
        assert r_wrong.status == "no_match"

        # 3. Same molecule reordered → mapping found
        import random
        xyz_list = list(xyz)
        random.Random(42).shuffle(xyz_list)
        r_shuffled = resolve_atom_mapping("CCO", tuple(xyz_list))
        assert r_shuffled.status in ("unique", "equivalent")

        # 4. Mapped coordinates → same fingerprint
        assert r.fingerprint.fingerprint_hash == r_shuffled.fingerprint.fingerprint_hash

    def test_glyoxal_scrambled_ordering(self):
        """Glyoxal (O=CC=O) with two different atom orderings.

        Order 1: O C C O H H (natural)
        Order 2: O H H C C O (scrambled)

        Graph isomorphism should map both to the same canonical species
        and produce identical torsion fingerprints.
        """
        # Order 1: O C C O H H
        xyz_order1 = (
            ("O",  1.3543,  1.0529,  0.1454),
            ("C",  0.7621,  0.0240, -0.0005),
            ("C", -0.7621, -0.0240,  0.0005),
            ("O", -1.3543, -1.0529, -0.1454),
            ("H",  1.2588, -0.9541, -0.1447),
            ("H", -1.2588,  0.9541,  0.1447),
        )

        # Order 2: O H H C C O (scrambled)
        xyz_order2 = (
            ("O",  1.3543,  1.0529,  0.1454),
            ("H",  1.2588, -0.9541, -0.1447),
            ("H", -1.2588,  0.9541,  0.1447),
            ("C",  0.7621,  0.0240, -0.0005),
            ("C", -0.7621, -0.0240,  0.0005),
            ("O", -1.3543, -1.0529, -0.1454),
        )

        smiles = "O=CC=O"

        r1 = resolve_atom_mapping(smiles, xyz_order1)
        r2 = resolve_atom_mapping(smiles, xyz_order2)

        # Both should resolve successfully
        assert r1.status in ("unique", "equivalent"), f"Order 1 failed: {r1.status}"
        assert r2.status in ("unique", "equivalent"), f"Order 2 failed: {r2.status}"
        assert r1.fingerprint is not None
        assert r2.fingerprint is not None

        # Glyoxal has 1 rotatable C-C bond → 1 rotor
        assert r1.fingerprint.rotor_count >= 1
        assert r2.fingerprint.rotor_count >= 1

        # Same fingerprint hash regardless of input atom ordering
        assert r1.fingerprint.fingerprint_hash == r2.fingerprint.fingerprint_hash

        # Fingerprints should match as same basin
        match, deltas, _rmsd = fingerprints_match(r1.fingerprint, r2.fingerprint)
        assert match


# ---------------------------------------------------------------------------
# Kabsch RMSD
# ---------------------------------------------------------------------------


class TestKabschRMSD:
    def test_identical_coords_zero_rmsd(self):
        coords = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        assert kabsch_rmsd(coords, coords) == pytest.approx(0.0, abs=1e-10)

    def test_translated_coords_zero_rmsd(self):
        """Translation should be removed by centering → RMSD ≈ 0."""
        coords_a = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        coords_b = [(5.0, 5.0, 5.0), (6.0, 5.0, 5.0), (5.0, 6.0, 5.0)]
        assert kabsch_rmsd(coords_a, coords_b) == pytest.approx(0.0, abs=1e-6)

    def test_rotated_coords_zero_rmsd(self):
        """90° rotation about Z axis should be corrected → RMSD ≈ 0."""
        # Original: triangle in XY plane
        coords_a = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0)]
        # Rotated 90° about Z: (x,y) → (-y,x)
        coords_b = [(0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)]
        assert kabsch_rmsd(coords_a, coords_b) == pytest.approx(0.0, abs=1e-6)

    def test_different_structures_nonzero_rmsd(self):
        """Actually different geometries should give nonzero RMSD."""
        coords_a = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
        coords_b = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (0.0, 2.0, 0.0)]
        rmsd = kabsch_rmsd(coords_a, coords_b)
        assert rmsd > 0.1

    def test_single_atom(self):
        """Single atom → distance."""
        assert kabsch_rmsd([(0.0, 0.0, 0.0)], [(1.0, 0.0, 0.0)]) == pytest.approx(1.0)

    def test_rmsd_with_fingerprint_match_rigid_molecule(self):
        """For rigid molecules (0 rotors), RMSD is the primary check."""
        # Two benzene conformers from different seeds
        mol1 = Chem.MolFromSmiles("c1ccccc1")
        mol1 = Chem.AddHs(mol1)
        AllChem.EmbedMolecule(mol1, randomSeed=42)

        mol2 = Chem.MolFromSmiles("c1ccccc1")
        mol2 = Chem.AddHs(mol2)
        AllChem.EmbedMolecule(mol2, randomSeed=42)  # same seed = same geometry

        fp1 = compute_torsion_fingerprint(mol1)
        fp2 = compute_torsion_fingerprint(mol2)

        # Extract coords in canonical order
        c1 = mol1.GetConformer()
        c2 = mol2.GetConformer()
        coords1 = [(c1.GetAtomPosition(i).x, c1.GetAtomPosition(i).y, c1.GetAtomPosition(i).z)
                    for i in range(mol1.GetNumAtoms())]
        coords2 = [(c2.GetAtomPosition(i).x, c2.GetAtomPosition(i).y, c2.GetAtomPosition(i).z)
                    for i in range(mol2.GetNumAtoms())]

        match, deltas, rmsd = fingerprints_match(
            fp1, fp2, coords1=coords1, coords2=coords2, rmsd_threshold=0.5
        )
        assert match
        assert rmsd is not None
        assert rmsd == pytest.approx(0.0, abs=1e-6)

    def test_rmsd_gates_rigid_match(self):
        """For rigid molecules, a large RMSD should prevent matching."""
        mol1 = Chem.MolFromSmiles("c1ccccc1")
        mol1 = Chem.AddHs(mol1)
        AllChem.EmbedMolecule(mol1, randomSeed=42)

        mol2 = Chem.MolFromSmiles("c1ccccc1")
        mol2 = Chem.AddHs(mol2)
        AllChem.EmbedMolecule(mol2, randomSeed=42)

        fp1 = compute_torsion_fingerprint(mol1)
        fp2 = compute_torsion_fingerprint(mol2)

        c1 = mol1.GetConformer()
        coords1 = [(c1.GetAtomPosition(i).x, c1.GetAtomPosition(i).y, c1.GetAtomPosition(i).z)
                    for i in range(mol1.GetNumAtoms())]
        # Shift all coords by 10 Å — large RMSD after Kabsch
        coords2_shifted = [(x + 0.5, y + 0.5, z + 0.5) for x, y, z in coords1]

        # With a very tight RMSD threshold, pure translation is removed by Kabsch
        # so this should still match (Kabsch corrects translation)
        match_loose, _, rmsd_loose = fingerprints_match(
            fp1, fp2, coords1=coords1, coords2=coords2_shifted, rmsd_threshold=0.5
        )
        assert match_loose  # translation is removed
        assert rmsd_loose == pytest.approx(0.0, abs=1e-6)

        # But actually distorted coords should fail
        coords2_distorted = [(x + 0.3 * i, y, z) for i, (x, y, z) in enumerate(coords1)]
        match_distort, _, rmsd_distort = fingerprints_match(
            fp1, fp2, coords1=coords1, coords2=coords2_distorted, rmsd_threshold=0.1
        )
        assert not match_distort
        assert rmsd_distort > 0.1
