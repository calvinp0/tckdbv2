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

6. **Handle symmetry-equivalent rotor permutations:**
   - Graph symmetry can create multiple equivalent rotor orderings.
   - Partition rotor slots into symmetry-equivalent classes.
   - Generate all admissible permutations, normalize each, keep the lexicographically minimal representation.
   - For most molecules this is trivial; for highly symmetric ones, pruning may be needed.

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

- **Rigid/small molecules** (0 or 1 rotor): same species entry + optional RMSD sanity check + optional energy window. Parameters stored in the scheme.
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
- If multiple heavy-atom mappings exist (molecular symmetry), compute the torsion fingerprint under each mapping. If all mappings produce the same fingerprint → accept as `equivalent`. If they disagree → reject as `conflicting` (unresolvable ambiguity).
- Outcome: atom-mapped coordinates in canonical species order, or rejection with diagnostic status.

**Step 2 — Torsion fingerprint (primary, for flexible molecules)**

Once atoms are mapped into canonical order, compute dihedrals for each canonical rotor slot and compare using circular difference with symmetry folding. This is the primary conformer basin discriminator for molecules with rotatable bonds.

**Step 3 — Kabsch RMSD (secondary, especially for rigid molecules)**

For rigid molecules with zero rotatable bonds, the torsion fingerprint is empty and cannot distinguish geometry differences. Kabsch alignment finds the optimal rotation minimizing RMSD between the two mapped coordinate sets (after centering on centroids via SVD). This serves as:
- The primary check for rigid molecules when `rmsd_threshold` is set.
- A secondary sanity check for flexible molecules (optional).

### Code Locations

- `app/chemistry/torsion_fingerprint.py`: Core module implementing all three steps:
  - `resolve_atom_mapping()` → `AtomMappingResult` — Step 1. Uses SMILES as graph truth with `DetermineConnectivity` as primary and SMILES-graph-only as fallback. Returns status (`unique`, `equivalent`, `conflicting`, `no_match`, `error`), the atom mapping, fingerprint, and mapped coordinates.
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
- Atom mapping status (`unique`, `equivalent`, `conflicting`)
- Scheme version and parameters used
- Number of valid graph isomorphisms found

RMSD is **not** part of the identity because it is relative to a chosen representative and changes if the representative is updated, the alignment is recomputed, or thresholds are adjusted.

## Limitations & Future Work

- **Ring conformers** (chair/boat, envelope/twist) are not well-described by simple dihedral comparison. Ring puckering parameters (Cremer–Pople) may be needed for cyclic systems. Kabsch RMSD partially addresses this as a fallback.
- **Symmetry-equivalent rotor permutations** — the current implementation deduplicates by heavy-atom mapping but does not yet generate all symmetry-equivalent rotor orderings and canonicalize to the lexicographic minimum. This is correct for most molecules but may produce false negatives for highly symmetric species.
- **XYZ-to-graph bond inference** uses `rdDetermineBonds.DetermineConnectivity` as the primary path, which may occasionally produce incorrect connectivity for unusual bond lengths, radicals, or charged species. Mitigated by: (a) the system rejects mismatches (`no_match` status) rather than silently accepting bad mappings, and (b) a fallback path uses the SMILES graph as the sole source of truth with element-based atom assignment when connectivity inference fails.
- **Threshold tuning** per molecule class could be a future scheme parameter (stricter for rigid molecules, more permissive for flexible chains).
- **Method-aware grouping**: two conformers optimized at very different levels of theory may produce different basin assignments. The scheme could optionally factor in LOT compatibility.
- The label-based fallback and imported-conformer scope provide graceful degradation when torsion data is unavailable.

## References

- CREST conformer sampling: Pracht, Bohle, Grimme, *PCCP* 2020, 22, 7169–7192. doi:10.1039/C9CP06869D
- Kabsch alignment: Kabsch, *Acta Crystallographica A* 1976, 32, 922–923. doi:10.1107/S0567739476001873
- RDKit conformer generation: `AllChem.EmbedMultipleConfs`, torsion-aware embedding with RMSD deduplication
- Cremer–Pople ring puckering: Cremer, Pople, *JACS* 1975, 97, 1354–1358. doi:10.1021/ja00839a011
- DR-0004: Calculation Structure-Level Provenance (conformer observation anchoring)
