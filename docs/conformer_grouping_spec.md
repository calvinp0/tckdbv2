# Conformer Group Assignment by Torsional Basin Matching

## Purpose

Assign conformer observations to conformer groups based on the torsional potential energy surface, replacing label-based matching with a scientifically meaningful comparison of molecular geometry.

## Scope

This specification covers the implemented `torsion_basin_v1` conformer assignment scheme. It applies to all conformer observations uploaded to TCKDB for species entries with resolved SMILES and 3D coordinates. It does **not** cover:

- Species identity resolution (stereoisomers, protonation states, connectivity) — these are resolved upstream at the `species_entry` level.
- Ring conformers (chair/boat, envelope/twist) — not well-described by simple dihedral comparison; Cremer–Pople puckering parameters may be needed.
- Imported literature conformers without geometry — these use a retained label-based fallback with `scope = "imported"`.

## Current Rule

**`torsion_basin_v1`**: Two conformer observations belong to the same conformer group if and only if **all** comparable torsion angles (measured at canonical rotor slots) differ by ≤ 15° under circular difference with symmetry folding, after resolving atom mapping via graph isomorphism from SMILES.

For rigid molecules (0 rotors): Kabsch-aligned RMSD ≤ 0.5 Å is the primary discriminator.

## Definitions

| Term | Definition |
|------|-----------|
| **Conformer observation** | A single uploaded 3D geometry for a species entry, with provenance |
| **Conformer group** | A set of observations occupying the same torsional basin |
| **Rotor slot** | A canonical rotatable bond eligible for dihedral comparison |
| **Canonical key** | `R_{rank_lo}_{rank_hi}` — species-invariant identifier for a rotor slot, based on RDKit canonical atom ranks |
| **Torsion fingerprint** | Ordered vector of raw, folded, and quantized dihedral angles at canonical rotor slots |
| **Fingerprint hash** | SHA-256 of (rotor keys + quantized bins + bin width) — an indexing key for fast DB lookup, not the authoritative identity check |
| **Circular difference** | `min(|θ₁ - θ₂| mod P, P - |θ₁ - θ₂| mod P)` where P is the period |
| **Symmetry fold** | Modular reduction of angle by rotor symmetry number σ: maps to [0°, 360°/σ) |
| **Graph automorphism** | A valid atom permutation that preserves the molecular graph (e.g., Cl swaps in CCl₃) |
| **Lexicographic minimization** | Choosing the smallest quantized bin vector among all valid mappings as the canonical form |
| **Representative fingerprint** | The fingerprint of the first accepted observation in a conformer group — an actual observed conformer, not an averaged angle vector |
| **Kabsch RMSD** | Root-mean-square deviation after optimal rotation alignment (SVD-based), computed on mapped coordinates |

## Decision Procedure

### Step 1 — Graph isomorphism (atom mapping)

1. Build the reference molecular graph from the species' SMILES (with hydrogens). **SMILES is the authoritative source of connectivity.**
2. **Primary path:** Infer connectivity from the uploaded XYZ using `rdDetermineBonds.DetermineConnectivity`. Run bond-order-agnostic graph isomorphism (`GetSubstructMatches`) to find all valid atom mappings.
3. **Fallback path:** If connectivity inference fails, fall back to SMILES-graph-only matching with element-based atom assignment. This avoids relying on fragile bond inference for radicals, TSs, or stretched bonds.
4. Deduplicate mappings by heavy-atom assignment (hydrogen permutations are irrelevant — terminal atom selection is deterministic via canonical ranking).
5. Resolve mapping multiplicity:
   - **1 heavy-atom mapping** → status `unique`
   - **Multiple mappings, all produce the same fingerprint** → status `equivalent`
   - **Multiple mappings, different fingerprints** → resolve via lexicographic minimization of the quantized bin vector → status `canonicalized`
   - **No valid mapping found** → status `no_match` → pipeline halts

### Step 2 — Torsion fingerprint (for flexible molecules)

6. Identify canonical rotor slots from the SMILES-derived molecular graph:
   - Single, non-ring, non-hydrogen bonds only
   - Exclude "both-terminal" bonds (both sides ≤ 1 heavy neighbor, e.g., ethane) — dihedrals defined only by H positions
   - Optionally exclude methyl rotors (`exclude_methyl_rotors` parameter)
   - Exclude terminal-noisy rotors (one side has no heavy neighbors besides bond partner) unless the side is a recognized methyl
7. For each rotor slot, determine the canonical dihedral quartet A–B–C–D:
   - Central atoms ordered by canonical rank (smaller first)
   - Terminal atoms chosen as the lowest-canonical-rank non-central heavy neighbor (H as fallback)
8. Compute the dihedral angle, normalize to [0°, 360°).
9. Apply symmetry folding:
   - σ = 1 → no fold (full 360°)
   - σ = 2 → mod 180°
   - σ = 3 (methyl on one side) → mod 120°
   - σ = 6 (methyl on both sides) → mod 60°
10. Quantize into bins: `bin_idx = int(folded / bin_width) % int(period / bin_width)`.

### Step 3 — Compare against existing groups

11. For each existing conformer group of the same species entry:
    - Reconstruct the representative fingerprint from stored JSONB
    - Compute circular difference per rotor (using the folded period for symmetric rotors)
    - **All** differences must be ≤ threshold → same basin
12. If multiple groups match, choose the one with the smallest total torsional distance. If tied, choose the earliest-created group.
13. **For rigid molecules** (0 rotors): Kabsch-aligned RMSD ≤ `rmsd_threshold_angstrom` is the primary discriminator when `rigid_fallback_use_rmsd` is enabled.
14. If no group matches, create a new conformer group with the observation's fingerprint and mapped coordinates as the representative.

### Step 4 — Fallback for trivial cases

15. If fingerprint computation fails (single atoms, bond inference failure): join the first existing group that also has no fingerprint, to prevent proliferation of empty groups.

## Thresholds and Boundaries

| Parameter | Value | Boundary | Notes |
|-----------|-------|----------|-------|
| `torsion_match_threshold_degrees` | 15.0° | Inclusive (≤) | 14.9° → pass, 15.0° → pass, 15.1° → fail |
| `rmsd_threshold_angstrom` | 0.5 Å | Inclusive (≤) | For rigid molecules only |
| `quantization_bin_degrees` | 15.0° | — | Fast prefilter; precise comparison is authoritative |
| `methyl_symmetry_fold` | 3 | — | Applied per-side; compounded to 6 for both-methyl bonds |
| `exclude_methyl_rotors` | false | — | Scheme parameter; when true, methyl-only molecules become effectively rigid |
| `exclude_terminal_noisy_rotors` | true | — | Filters bonds where one side has only H neighbors (unless methyl) |
| `rigid_fallback_use_rmsd` | true | — | Enables RMSD as primary check for 0-rotor molecules |

**Floating-point precision note:** Due to trigonometric arithmetic, angles mathematically at the boundary (e.g., 15.000000000000057°) may cross it. The threshold is a soft boundary, not a machine-precision cutoff.

## Special Cases

### Symmetry canonicalization (graph automorphisms)

When a molecule has equivalent substituents (e.g., CCl₃ in chloral), multiple valid atom mappings produce different fingerprints for the same geometry. Resolved by lexicographic minimization of the quantized bin vector. This guarantees: **two uploads of the same geometry, regardless of atom ordering, always produce the same canonical fingerprint.**

Consequence: mapped coordinates may differ between canonicalized mappings of identical geometry (e.g., ~1.56 Å RMSD for chloral Cl↔Cl swap distance). This is acceptable because torsion fingerprint, not coordinates, is the identity metric for flexible molecules.

### Methyl exclusion creating zero rotors

When `exclude_methyl_rotors=true` removes all rotors (e.g., ethanol CCO), the molecule becomes effectively rigid from the matcher's perspective. RMSD becomes the fallback discriminator. This is a design choice: the C-O rotation is scientifically meaningful but methyl-dominated.

### Both-terminal exclusion (ethane rule)

Bonds where both sides have ≤ 1 heavy neighbor (e.g., ethane CH₃–CH₃) are excluded from rotor discovery. Their dihedrals are defined only by hydrogen positions, which are too noisy for basin identity.

### Chirality safety

Graph isomorphism is bond-order-agnostic and not stereo-aware — an S geometry can successfully map onto R SMILES. Stereo enforcement belongs at the `species_entry` level, not conformer grouping. However, the torsion fingerprint provides a partial safety net: enantiomeric geometries produce different torsion angles (mirrored dihedral values), so they land in different basins even if stereo filtering were accidentally skipped.

### Rigid molecules (0 rotors)

The torsion fingerprint is empty. Kabsch RMSD is the primary check when `rigid_fallback_use_rmsd` is enabled with a threshold. Without RMSD data, the default is to assign to the same group (cannot distinguish).

### RMSD for flexible molecules

RMSD is computed as diagnostic evidence (if coordinates are provided) but does **not** gate the basin decision. It is stored for audit purposes.

### Atom-order invariance

The canonical fingerprint is built from the SMILES molecular graph, not the input XYZ ordering. Graph isomorphism maps every input ordering to the same canonical species graph. Verified on 7 molecules with original + shuffled orderings.

## Examples

### Positive match (same basin)

**ClCCO gauche vs gauche-prime (~10° apart):**
- Gauche: Cl-C-C-O dihedral ≈ 60°
- Gauche-prime: Cl-C-C-O dihedral ≈ 70°
- Circular difference: ~10° < 15° threshold
- Result: `same_basin=True`, Kabsch RMSD < 0.2 Å

### Negative match (different basin)

**ClCCO gauche vs anti:**
- Gauche: Cl-C-C-O dihedral ≈ 60°
- Anti: Cl-C-C-O dihedral ≈ 180°
- Circular difference: ~120° >> 15° threshold
- Result: `same_basin=False`, Kabsch RMSD > 0.5 Å

### Multi-rotor partial match (rejected)

**Pentane [60°, 60°] vs [70°, 76°]:**
- Rotor 1 delta: ~10° < 15° → pass
- Rotor 2 delta: ~16° > 15° → fail
- Result: `same_basin=False` — all torsions must pass, not an aggregate metric

### Canonicalization (symmetric molecule)

**Chloral (O=CC(Cl)(Cl)Cl):**
- 6 valid heavy-atom mappings (3! Cl permutations × 2 H permutations)
- 3 distinct fingerprints (each Cl permutation shifts the dihedral by ~120°)
- Lexicographic minimization chooses the smallest bin vector as canonical
- Verified with 13 atom-ordering variants: all produce identical canonical fingerprint

## Known Limitations

1. **Ring conformers** (chair/boat, envelope/twist) are not well-described by simple dihedral comparison. Cremer–Pople puckering parameters may be needed.
2. **XYZ-to-graph bond inference** may produce incorrect connectivity for unusual bond lengths, radicals, or charged species. Mitigated by: (a) `no_match` rejection rather than silent acceptance, and (b) SMILES-graph-only fallback.
3. **Threshold boundary precision:** floating-point trigonometric arithmetic can produce angles mathematically at the boundary that cross due to rounding (e.g., 15.000000000000057°). In practice negligible.
4. **Stereochemistry not enforced at fingerprint level.** The graph isomorphism is not stereo-aware. An S geometry can map onto R SMILES. Stereo enforcement is the responsibility of `species_entry`-level filtering. The torsion fingerprint provides a partial (but not guaranteed) safety net via mirrored dihedral values.
5. **Canonicalization stabilizes fingerprints, not mapped coordinates.** Two orderings of the same geometry may select different atom assignments as canonical if multiple mappings produce the same minimal fingerprint.
6. **Symmetry fold is a scheme decision**, not automatically detected from molecular topology. Incorrect fold parameters would produce wrong basin assignments.
7. **Reconstructed fingerprints from JSONB lose symmetry_fold information.** The `_reconstruct_fingerprint()` function sets `symmetry_fold=1` for all reconstructed slots. This means comparison against stored representatives uses unfolded circular difference (period=360°), which is more conservative but correct when the stored folded values are already folded.

## Open Questions

1. **Per-molecule-class threshold tuning:** Should specific molecule classes (e.g., rigid vs flexible chains) use different thresholds? Currently a single threshold applies globally via the scheme.
2. **Method-aware grouping:** Two conformers optimized at very different levels of theory may produce different basin assignments. Should the scheme optionally factor in LOT compatibility?
3. **Energy sanity check:** Energy should not define the group, but two structures with similar torsions and wildly different energies may indicate failed optimization. Should the scheme include an optional energy-window sanity check?
4. **Stable mapped coordinates:** If coordinate-based deduplication is needed in the future, the canonicalization can be extended with a secondary tiebreaker (RMSD to reference geometry among lex-min-tied mappings). Is this needed?
5. **Ring puckering parameters:** When should Cremer–Pople parameters be integrated, and should they be a separate scheme or an extension of `torsion_basin`?
6. **Label-based fallback scope:** The current fallback for imported conformers without geometry uses label matching. What happens when geometry becomes available for previously label-matched conformers — should they be re-evaluated?

## Test-Backed Behavior

The following behaviors are verified by the test suite (`tests/test_torsion_fingerprint.py`, 79 tests):

1. **Atom-order invariance** (7 molecules × 2 orderings): Same geometry with scrambled atom ordering produces identical fingerprint hash. Tested on ClCCO, ClCCN, ClCCCl, CC(Cl)CO, ClCC=O, chloral, bis-CF₂.
2. **Symmetry canonicalization:** Single-rotor (chloral: 6 mappings → 3 fingerprints) and multi-rotor (bis-CF₂: 8 mappings → 7 fingerprints) molecules produce consistent canonical fingerprints via lexicographic minimization.
3. **Conformer discrimination:** Gauche (~60°) vs anti (~180°) rotamers correctly separated for ClCCO, ClCCN, ClCCCl, ClCC=O. Gauche vs gauche-prime (~10° apart) correctly grouped.
4. **Threshold boundary:** 14.9° → pass, 15.0° → pass (≤), 15.1° → fail. Wraparound near 0°/360° works correctly (7° vs 353° = 14° → pass).
5. **Multi-rotor "all must pass" rule:** Pentane with one torsion within threshold and one outside → correctly rejected. Not an aggregate metric.
6. **Rotor-order stability:** Canonical rotor keys and ordering identical across shuffled atom orderings for multi-rotor molecules (pentane, CC(Cl)CO).
7. **Chirality safety:** R/S enantiomers of 2-chloro-1-propanol produce different torsion fingerprints and are not merged (`same_basin=False`).
8. **Methyl-exclusion fallback:** Ethanol with `exclude_methyl=True` → 0 rotors → RMSD becomes primary discriminator. Same geometry matches; distorted geometry rejected.
9. **Stereocenter-adjacent rotor:** (R)-2-butanol with rotor next to chiral center resolves correctly; fingerprint stable across atom orderings.
10. **All-mapping consistency:** For every tested symmetric molecule, all valid graph isomorphisms are enumerated and the canonical choice equals the lexicographic minimum of the full set.
11. **Ethane rule:** Ethane (CC) produces 0 rotor slots — both-terminal bonds excluded by design.
12. **Rigid molecule default match:** Benzene (all bonds in ring) → 0 rotors → two conformers match by default when no RMSD data is provided.
13. **RMSD gates rigid matching:** For rigid molecules, Kabsch-aligned RMSD correctly passes identical geometries and rejects distorted geometries.
14. **Hash includes rotor structure:** Two fingerprints with identical quantized bins but different rotor keys produce different hashes.
15. **Cross-molecule rejection:** ClCCO geometry correctly produces `no_match` when mapped against ClCCN SMILES.
16. **Single atom handling:** `[H]` atom produces a valid fingerprint with 0 rotors.
17. **Glyoxal scrambled ordering:** O=CC=O with two different atom orderings produces identical fingerprint hashes.

## Code Locations

| Component | File | Entry Point |
|-----------|------|-------------|
| Core fingerprint logic | `app/chemistry/torsion_fingerprint.py` | `compute_torsion_fingerprint()` |
| Atom mapping + canonicalization | `app/chemistry/torsion_fingerprint.py` | `resolve_atom_mapping()` → `AtomMappingResult` |
| Kabsch RMSD | `app/chemistry/torsion_fingerprint.py` | `kabsch_rmsd()` |
| Conformer comparison | `app/chemistry/torsion_fingerprint.py` | `compare_conformers()` → `ConformerComparisonResult` |
| Conformer group resolution | `app/services/conformer_resolution.py` | `resolve_conformer_group()` |
| DB models | `app/db/models/species.py` | `ConformerGroup`, `ConformerObservation`, `ConformerAssignmentScheme` |
| Scheme parameters | `app/services/conformer_resolution.py` | `_DEFAULT_SCHEME_PARAMS` |
| Tests | `tests/test_torsion_fingerprint.py` | 79 tests across 13 test classes |
