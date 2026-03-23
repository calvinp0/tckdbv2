# DR-0005: Conformer Group Assignment by Torsional Basin Matching

**Date:** 2026-03-23
**Status:** Accepted
**Authors:** Calvin (scientific specification), Claude (implementation notes)

## Context

When multiple conformer observations are uploaded for the same species entry (e.g., from different computational studies, different users, or different Arkane runs), the system must decide whether two observations belong to the same conformational basin (same `conformer_group`) or represent distinct rotamers (different groups).

The previous implementation used a label-matching placeholder: if two uploads provided the same `label` string, they were grouped together; otherwise a new group was created. This is scientifically meaningless — it relies on naming conventions rather than molecular geometry.

For a thermochemical database, correct conformer grouping is critical because:
- Thermodynamic properties (partition functions, entropy) depend on which conformational basins are sampled
- Duplicate basins artificially inflate the conformer ensemble
- Missing basins lead to incomplete sampling and biased thermochemistry

## Considered Alternatives

### Alternative A: Label-only matching (previous)
- **Description:** Group by user-supplied string label.
- **Pros:** Simple, zero computation.
- **Cons / why rejected:** Not scientific. Two observations of the same basin get separate groups if labels differ. Two observations of different basins merge if labels happen to match.

### Alternative B: RMSD-based clustering
- **Description:** Compute RMSD between aligned geometries; group if below a threshold.
- **Pros:** Geometry-aware, well-established metric.
- **Cons / why rejected:** RMSD conflates torsional differences with bond-length/angle variations. Two conformers of a flexible molecule may have high RMSD even if they occupy the same torsional basin. Torsions are the natural coordinate for conformer identity.

### Alternative C: Energy-window clustering
- **Description:** Group conformers within a ΔE window (e.g., ±5 kJ/mol).
- **Pros:** Simple, energy-relevant.
- **Cons / why rejected:** Conformers in different basins can have similar energies. Energy is a property, not an identity. However, energy can serve as a sanity check (see below).

### Alternative D: Torsional basin matching with canonical fingerprint (chosen)
- **Description:** Compare torsion angles of canonical rotatable bonds using circular difference with a threshold (default 15°), using a symmetry-aware canonical fingerprint derived from the molecular graph.
- **Pros:** Directly reflects the conformational degree of freedom. Handles periodicity and symmetry. Parameterizable, versionable, and auditable.
- **Cons:** Requires torsion extraction, canonical rotor identification, and symmetry handling. Less meaningful for rigid molecules with few/no rotors (addressed by fallback rules).

## Decision

Conformer observations are assigned to existing conformer groups using a **canonical torsion fingerprint** built from a species-specific set of relevant rotatable bonds, compared using symmetry-aware circular difference.

### Core Algorithm

1. **Prerequisite:** Stereochemistry and bonding must already match before torsion grouping starts. The torsion logic never distinguishes different species entries, stereoisomers, protonation states, or connectivities — that is resolved upstream.

2. **Define the rotor universe** for the species entry (once per species, cached):
   - Identify relevant rotatable bonds: single, non-terminal, non-ring bonds by default.
   - Exclude low-information rotors (e.g., methyl tops) based on scheme parameters.
   - Each selected bond becomes a **rotor slot** in the fingerprint.

3. **Canonically identify each rotor slot:**
   - Determine a canonical atom labeling for the molecular graph (e.g., RDKit canonical ranking).
   - Identify each rotor by the ordered canonical bond key `(canon_b, canon_c)` with the smaller index first.
   - Choose canonical terminal atoms A, D deterministically (lowest-rank non-central neighbor on each side).
   - This makes rotor slots atom-order-independent.

4. **Extract torsion angles** for the new conformer observation:
   - For each canonical rotor slot, compute the dihedral angle using the canonical A–B–C–D quartet.
   - Normalize to `[0°, 360°)`.

5. **Fold by rotor symmetry** where scientifically justified:
   - Each rotor slot has an optional symmetry number σ (stored in the scheme).
   - σ = 1: no folding (compare in full 360°).
   - σ = 2 (e.g., symmetric substituent): compare modulo 180°.
   - σ = 3 (e.g., methyl top on one side): compare modulo 120°.
   - σ = 6 (methyl on both sides of a rotatable bond): compare modulo 60°. This arises because the 3-fold symmetry on each side compounds (3 × 2 = 6).
   - This is a scheme decision, not automatically applied everywhere.

6. **Handle symmetry-equivalent atom permutations (canonicalization):**

   This is one of the most subtle aspects of the system. When a molecule has graph automorphisms — meaning the molecular graph can be mapped onto itself in multiple valid ways — the graph isomorphism step (Step 1 of the pipeline) will find multiple valid atom mappings from XYZ to the reference SMILES. Each mapping can produce a **different** torsion fingerprint, even though the underlying geometry is identical.

   **Why this happens — concrete example:**

   Consider chloral, `O=CC(Cl)(Cl)Cl`. The three chlorine atoms are graph-equivalent: swapping any two Cl atoms produces a valid graph automorphism. When we run graph isomorphism between an uploaded XYZ and the SMILES-derived reference mol, we get 6 unique heavy-atom mappings (3! = 6 permutations of the three Cl atoms).

   The molecule has one rotatable bond: the C–C bond between the aldehyde carbon and the CCl₃ carbon. The canonical dihedral is A–B–C–D, where D is the terminal atom on the CCl₃ side chosen by lowest canonical rank. But which Cl gets chosen as D depends on the mapping — different Cl permutations place different Cl atoms at the D position. Since the three Cl atoms sit at roughly 120° intervals around the C–Cl₃ axis, the measured dihedral differs by ~120° between mappings:

   ```
   Mapping 0: dihedral =   0.0°  → bin [0]
   Mapping 1: dihedral = 121.5°  → bin [8]
   Mapping 2: dihedral = 238.5°  → bin [15]
   (each repeated twice due to additional H permutations → 6 total)
   ```

   All six mappings are chemically correct — they are equivalent representations of the same geometry. But they produce three distinct fingerprints. Without canonicalization, the system would declare `status=conflicting` and refuse to assign the conformer to any group.

   **The solution — lexicographic minimization:**

   When multiple valid mappings produce different fingerprints, the system picks the **lexicographically minimal** fingerprint (smallest quantized bin vector). This is the canonical form:

   ```
   Mapping 0: bins = [0]   ← smallest, chosen as canonical
   Mapping 1: bins = [8]
   Mapping 2: bins = [15]
   ```

   The key guarantee: **two uploads of the same geometry, regardless of atom ordering, will always produce the same canonical fingerprint.** This is because:
   - The set of valid graph isomorphisms is determined by the molecular graph (from SMILES), not by the input atom ordering.
   - Each valid isomorphism produces a deterministic fingerprint.
   - Lexicographic minimization over a fixed set always picks the same element.

   This was verified empirically: 13 different atom orderings of the same chloral geometry (reversed, Cl-shuffled, C+Cl-shuffled, 10 random full permutations) all produced `status=canonicalized` with identical fingerprint hashes and identical quantized bins.

   **Consequence for mapped coordinates:**

   Canonicalization stabilizes the **torsion fingerprint** but not necessarily the **atom mapping** itself. Two orderings of the same geometry may select different Cl→ref assignments as canonical (if multiple mappings produce the same minimal fingerprint). This means the mapped coordinates can differ, and Kabsch RMSD between two canonicalized mappings of identical geometry may be nonzero (observed: ~1.56 Å for chloral, equal to the Cl↔Cl swap distance).

   This is acceptable because:
   - For **flexible molecules**, torsion fingerprint is the identity metric, not RMSD.
   - For **rigid molecules** (0 rotors), the canonicalization produces identical fingerprints trivially (empty bin vector), and RMSD comparison uses a separate representative-geometry pathway.
   - If stable mapped coordinates are needed in the future (e.g., for coordinate-based deduplication), the canonicalization can be extended with a secondary tiebreaker: among all mappings producing the same minimal fingerprint, choose the one with the lowest RMSD to a reference geometry.

   **Resolution statuses:**

   The atom mapping step now reports one of four statuses:

   | Status | Meaning | Example |
   |--------|---------|---------|
   | `unique` | One heavy-atom mapping found | Ethanol (no symmetry) |
   | `equivalent` | Multiple mappings, all produce the same fingerprint | Propane (mirror symmetry — Cl swaps don't change torsions because there are no Cl torsions) |
   | `canonicalized` | Multiple mappings, different fingerprints — lexicographic minimum chosen | Chloral (CCl₃ 3-fold symmetry) |
   | `no_match` | No valid graph isomorphism found | Wrong element count, incompatible connectivity |

   All three resolved statuses (`unique`, `equivalent`, `canonicalized`) proceed to fingerprint comparison. Only `no_match` and `error` halt the pipeline.

7. **Compare against existing groups:**
   - Each `conformer_group` stores a representative canonical fingerprint (the medoid member).
   - Compute **minimum circular difference** per rotor: `min(|θ₁ - θ₂|, 360° - |θ₁ - θ₂|)` (after folding).
   - If **all** matched torsional differences are within the threshold → same group.
   - **Quantized bins** (bin width = threshold) serve as a fast prefilter before precise comparison.

8. **Tie-breaking** when multiple groups match:
   - Choose the group whose representative has the smallest total torsional distance.
   - If still tied, choose the earliest-created group.
   - Explicit, deterministic — never accidental.

9. **Handle undefined/ambiguous torsions:**
   - Near-linear arrangements can make dihedrals numerically unstable.
   - Compare only torsions that are valid and comparable under the scheme.
   - Missing or undefined torsions follow scheme-specific policy (ignore, or reject for manual resolution).

10. **Store assignment evidence:**
    - Not just "assigned to group 7," but also: compared torsions, per-torsion angular deltas, chosen representative, scheme version, assignment score.
    - Stored as JSONB on the `conformer_observation` or in a separate assignment-evidence table.

### Fingerprint Structure

For each conformer observation, store:

```
species_entry_id
assignment_scheme_id
rotor_count
canonical_rotor_keys        -- e.g., ["R1", "R2", "R3"]
raw_torsions_deg            -- e.g., [61.2, 178.5, 300.1]
folded_torsions_deg         -- e.g., [61.2, 58.5, 60.1]
quantized_bins              -- e.g., [4, 4, 4]
fingerprint_hash            -- SHA-256 of quantized bins for fast lookup (indexing, not truth)
```

**Important:** The `fingerprint_hash` is an **indexing key for fast DB lookup**, not the authoritative identity check. Two conformers whose hashes match are likely in the same basin. Two conformers whose hashes differ (due to quantization boundary effects, e.g., 14.9° → bin 0, 15.1° → bin 1) may still match under the precise circular-difference check. The two-step process is: (A) hash for fast candidate retrieval, (B) `compare_conformers()` for the actual decision.

Each `conformer_group` stores:
- A **representative fingerprint** (the first accepted observation — an actual observed conformer, not an averaged angle vector).
- **Representative mapped coordinates** (canonical atom order) for Kabsch RMSD comparison, especially critical for rigid molecules.

### Default Scheme Parameters

```json
{
    "name": "torsion_basin",
    "version": "v1",
    "parameters_json": {
        "require_all_comparable_torsions_within_threshold": true,
        "torsion_match_threshold_degrees": 15,
        "use_circular_difference": true,
        "exclude_methyl_rotors": false,
        "exclude_terminal_noisy_rotors": true,
        "methyl_symmetry_fold": 3,
        "quantization_bin_degrees": 15,
        "rigid_fallback_use_rmsd": true,
        "rmsd_threshold_angstrom": 0.5,
        "tie_break": "closest_torsional_distance"
    }
}
```

### Fallbacks

- **Rigid/small molecules** (0 rotors): same species entry + Kabsch RMSD comparison when `rigid_fallback_use_rmsd` is enabled. Parameters stored in the scheme.
- **Methyl-exclusion creates zero rotors**: when `exclude_methyl_rotors=true` removes all rotors from a molecule that has rotatable bonds (e.g., ethanol CCO), the molecule becomes effectively rigid from the matcher's perspective. RMSD then becomes the fallback discriminator. This is a design choice: ethanol's C-O rotation is scientifically meaningful but methyl-dominated, so excluding it trades conformer resolution for grouping stability.
- **Both-terminal exclusion (ethane rule)**: bonds where both sides have ≤1 heavy neighbor (e.g., ethane CH₃-CH₃) are excluded from rotor discovery because their dihedrals are defined only by hydrogen positions, which are too noisy for basin identity. This is an intentional design choice, not a limitation.
- **Label hint**: When torsion data is unavailable (e.g., imported literature conformers without geometry), the label-based fallback is retained with `scope = "imported"`.

## Scientific Justification

Conformational basins in flexible molecules are defined by the torsional potential energy surface. Two geometries that differ only by small oscillations around the same torsional minimum occupy the same basin; geometries separated by a torsional barrier occupy different basins.

A 15° threshold is consistent with the typical width of torsional minima in organic molecules. Most rotational barriers produce basins with widths of 30–60° at room temperature. A 15° tolerance:
- Correctly groups re-optimized geometries of the same basin (which may differ by a few degrees depending on level of theory or optimization convergence)
- Separates distinct rotamers (which typically differ by ≥60° in at least one torsion)
- Is consistent with the tolerance used in CREST (Pracht et al., 2020) and RDKit's conformer deduplication

The `require_all_comparable_torsions_within_threshold` rule is conservative: a single mismatched torsion separates two conformers. This is correct because a molecule can differ in one dihedral while being identical in all others, and that one difference defines a distinct rotamer.

Energy should **not** define the group, but can sanity-check it. Two structures with similar torsions but wildly different energies may indicate failed optimization or different local minima not captured by the torsion list.

The canonical fingerprint — built from a canonical, species-specific list of relevant rotors, with deterministic dihedral definitions, symmetry folding, and symmetry-equivalent permutation canonicalization — ensures that atom ordering, equivalent substituent swaps, and periodic angle representation do not break matching.

## Implementation Notes

### Three-Step Comparison Pipeline

The conformer comparison system operates as a three-step pipeline, each solving a distinct problem:

**Step 1 — Graph isomorphism (atom mapping)**

Before any geometric comparison, the system must establish which atom in one geometry corresponds to which atom in another. This is a topology matching problem, not a 3D problem. **The SMILES string is the authoritative source of molecular graph topology; the XYZ provides only geometry (coordinates).**

- Build the reference molecular graph from the species' SMILES (with hydrogens) — this is the single source of truth for connectivity.
- **Primary path:** Build a provisional graph from the uploaded XYZ by inferring connectivity from 3D distances (`rdDetermineBonds.DetermineConnectivity`). Run graph isomorphism (`GetSubstructMatches` with bond-order-agnostic matching) to find all valid atom mappings. This works well for typical geometries.
- **Fallback path:** If connectivity inference fails (fragile for radicals, TSs, stretched bonds, weak interactions), fall back to SMILES-graph-only matching with element-based assignment. This avoids relying on fragile bond inference and trusts SMILES as the complete graph definition.
- Deduplicate by heavy-atom mapping (hydrogen permutations are irrelevant for torsion comparison since terminal atom selection is deterministic via canonical ranking).
- If multiple heavy-atom mappings exist (molecular symmetry), compute the torsion fingerprint under each mapping. If all mappings produce the same fingerprint → accept as `equivalent`. If they disagree → resolve via lexicographic minimization of the quantized bin vector → `canonicalized` (see Step 6 in Core Algorithm).
- Verified on both single-rotor (chloral: 6 mappings → 3 fingerprints) and multi-rotor (bis-CF₂ `CC(F)(F)CC(F)(F)C`: 8 mappings → 7 fingerprints) symmetric molecules.
- Outcome: atom-mapped coordinates in canonical species order, or rejection with diagnostic status.

**Step 2 — Torsion fingerprint (primary, for flexible molecules)**

Once atoms are mapped into canonical order, compute dihedrals for each canonical rotor slot and compare using circular difference with symmetry folding. This is the primary conformer basin discriminator for molecules with rotatable bonds.

**Step 3 — Kabsch RMSD (secondary, especially for rigid molecules)**

For rigid molecules with zero rotatable bonds, the torsion fingerprint is empty and cannot distinguish geometry differences. Kabsch alignment finds the optimal rotation minimizing RMSD between the two mapped coordinate sets (after centering on centroids via SVD). This serves as:
- The primary check for rigid molecules when `rmsd_threshold` is set.
- A secondary sanity check for flexible molecules (optional).

### Code Locations

- `app/chemistry/torsion_fingerprint.py`: Core module implementing all three steps:
  - `resolve_atom_mapping()` → `AtomMappingResult` — Step 1. Uses SMILES as graph truth with `DetermineConnectivity` as primary and SMILES-graph-only as fallback. When multiple valid mappings produce different fingerprints (graph automorphisms), resolves via lexicographic minimization. Returns status (`unique`, `equivalent`, `canonicalized`, `no_match`, `error`), the atom mapping, fingerprint, and mapped coordinates.
  - `compute_torsion_fingerprint()` → `TorsionFingerprint` — Step 2 (canonical rotor extraction + dihedral computation).
  - `kabsch_rmsd()` — Step 3 (Kabsch-aligned RMSD via SVD).
  - `compare_conformers()` → `ConformerComparisonResult` — The primary comparison function. Explicitly separates `same_basin` (identity decision) from `torsion_deltas` and `kabsch_rmsd` (diagnostic evidence). Uses torsion fingerprint for flexible molecules, Kabsch RMSD for rigid molecules.
  - `fingerprints_match()` — Backward-compatible wrapper around `compare_conformers()`.
- `app/services/conformer_resolution.py`: `resolve_conformer_group()` — wires the fingerprint system into the conformer upload workflow. Calls `resolve_atom_mapping()` to get both fingerprint and mapped coords. Matches against existing group representatives (torsion + RMSD for rigid). Stores representative fingerprint and representative coords when creating new groups.
- `app/db/models/species.py`:
  - `conformer_observation.torsion_fingerprint_json` (JSONB) — stores each observation's fingerprint
  - `conformer_group.representative_fingerprint_json` (JSONB) — stores the group's representative fingerprint for matching
  - `conformer_group.representative_coords_json` (JSONB) — stores mapped coordinates (canonical atom order) for Kabsch RMSD comparison against new observations
  - `conformer_observation.assignment_scheme_id` FK — references the scheme used for assignment
- `conformer_assignment_scheme` table: seeded with `torsion_basin_v1` default scheme containing all parameters.
- All three conformer creation paths are wired (conformer upload, network PDep, computed reaction).

### Conformer Group Identity vs Assignment Evidence

**Identity** (what defines a conformer group):

- `species_entry` = molecular identity (what molecule)
- `assignment_scheme` = which grouping rule version was applied
- **For flexible molecules** (rotors > 0): canonical torsion basin, keyed by `torsion_fingerprint_hash`
- **For rigid molecules** (rotors = 0): geometry similarity under mapped Kabsch alignment

The persisted stable identity is `conformer_group.id` — the tuple above is the decision logic that determines group assignment, not a floating composite key.

**Assignment evidence** (how the decision was made — stored for audit, not for identity):

- Kabsch RMSD to the group representative
- Per-rotor angular deltas
- Atom mapping status (`unique`, `equivalent`, `canonicalized`)
- Scheme version and parameters used
- Number of valid graph isomorphisms found

RMSD is **not** part of the identity because it is relative to a chosen representative and changes if the representative is updated, the alignment is recomputed, or thresholds are adjusted.

## Verified Properties

The following properties are verified by the test suite (`tests/test_torsion_fingerprint.py`, 79 tests):

1. **Atom-order invariance**: Same geometry with scrambled atom ordering → identical fingerprint hash. Tested on 7 molecules (ClCCO, ClCCN, ClCCCl, CC(Cl)CO, ClCC=O, chloral, bis-CF₂) with original + shuffled orderings.
2. **Symmetry canonicalization**: Molecules with graph automorphisms produce consistent canonical fingerprints via lexicographic minimization. Single-rotor (chloral, 6 mappings) and multi-rotor (bis-CF₂, 8 mappings) cases verified.
3. **Conformer discrimination**: Gauche (60°) vs anti (180°) rotamers correctly separated for 4 molecules. Gauche vs gauche-prime (10° apart) correctly grouped.
4. **Threshold boundary**: 14.9° → pass, 15.0° → pass (≤), 15.1° → fail. Wraparound near 0°/360° works correctly.
5. **Multi-rotor "all must pass" rule**: Pentane with one torsion within threshold and one outside → correctly rejected. Not an aggregate metric.
6. **Rotor-order stability**: Canonical rotor keys and ordering identical across shuffled atom orderings for multi-rotor molecules.
7. **Chirality safety**: R/S enantiomers of 2-chloro-1-propanol produce different torsion fingerprints and are not merged (`same_basin=False`).
8. **Methyl-exclusion fallback**: Ethanol with `exclude_methyl=True` → 0 rotors → RMSD becomes primary discriminator. Same geometry matches; distorted geometry rejected.
9. **Stereocenter-adjacent rotor**: (R)-2-butanol with rotor next to chiral center resolves correctly; fingerprint stable across atom orderings.
10. **All-mapping consistency**: For every tested symmetric molecule, all valid graph isomorphisms are enumerated and the canonical choice equals the lexicographic minimum of the full set.

## Limitations & Future Work

- **Ring conformers** (chair/boat, envelope/twist) are not well-described by simple dihedral comparison. Ring puckering parameters (Cremer–Pople) may be needed for cyclic systems. Kabsch RMSD partially addresses this as a fallback.
- **Symmetry-equivalent rotor permutations** — resolved in the current implementation via lexicographic minimization of fingerprints across all valid graph automorphisms (see Step 6 above). Verified on chloral (CCl₃, 6 heavy-atom permutations) with 13 atom-ordering variants. The consequence is that mapped coordinates may differ between canonicalized mappings of identical geometry; if stable coordinate identity is needed, a secondary RMSD-based tiebreaker can be added.
- **XYZ-to-graph bond inference** uses `rdDetermineBonds.DetermineConnectivity` as the primary path, which may occasionally produce incorrect connectivity for unusual bond lengths, radicals, or charged species. Mitigated by: (a) the system rejects mismatches (`no_match` status) rather than silently accepting bad mappings, and (b) a fallback path uses the SMILES graph as the sole source of truth with element-based atom assignment when connectivity inference fails.
- **Stereochemistry enforcement** is not handled at the conformer fingerprint level. The graph isomorphism uses bond-order-agnostic matching and does not enforce R/S chirality — an S geometry can successfully map onto R SMILES. This is by design: stereo enforcement belongs at the `species_entry` level (via `stereo_kind` and `stereo_label`), not at conformer grouping. By the time two geometries reach conformer comparison, they should already be confirmed as the same stereoisomer. However, the torsion fingerprint provides a partial safety net: enantiomeric geometries typically produce different torsion angles (mirrored dihedral values), so they would land in different basins even if stereo filtering were accidentally skipped. This was verified with R/S enantiomers of 2-chloro-1-propanol (`C[C@H](Cl)CO` vs `C[C@@H](Cl)CO`).
- **Threshold boundary precision**: the comparison uses `<=` (delta ≤ threshold), so exactly 15.0° is a pass. Due to floating-point arithmetic in trigonometric functions, angles that are mathematically exactly at the boundary (e.g., 15.000000000000057°) may cross it. In practice this is negligible, but the scheme's `torsion_match_threshold_degrees` should be understood as a soft boundary, not a machine-precision cutoff. Verified with tests at 14.9°, 15.0°, and 15.1° separations.
- **Threshold tuning** per molecule class could be a future scheme parameter (stricter for rigid molecules, more permissive for flexible chains).
- **Method-aware grouping**: two conformers optimized at very different levels of theory may produce different basin assignments. The scheme could optionally factor in LOT compatibility.
- The label-based fallback and imported-conformer scope provide graceful degradation when torsion data is unavailable.

## References

- CREST conformer sampling: Pracht, Bohle, Grimme, *PCCP* 2020, 22, 7169–7192. doi:10.1039/C9CP06869D
- Kabsch alignment: Kabsch, *Acta Crystallographica A* 1976, 32, 922–923. doi:10.1107/S0567739476001873
- RDKit conformer generation: `AllChem.EmbedMultipleConfs`, torsion-aware embedding with RMSD deduplication
- Cremer–Pople ring puckering: Cremer, Pople, *JACS* 1975, 97, 1354–1358. doi:10.1021/ja00839a011
- DR-0004: Calculation Structure-Level Provenance (conformer observation anchoring)
