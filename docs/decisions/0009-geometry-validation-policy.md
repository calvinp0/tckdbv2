# DR-0009: Geometry Validation Policy — Graph Isomorphism as Hard Gate

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

When a user uploads a species optimization calculation, the final optimized geometry should correspond to the claimed species identity. However, optimizations can produce unexpected results: proton transfers, tautomerizations, dissociations, bond rearrangements, or simply wrong-job uploads. The database needs a validation mechanism to catch these failures.

Naive coordinate equality checking is wrong for this purpose: atom ordering may differ, molecular orientation will differ (rotation/translation), symmetry may reorder atoms, and internal vs Cartesian coordinate representations are not directly comparable.

## Considered Alternatives

### Alternative A: No validation — trust the uploader

- **Description:** Accept whatever the user claims.
- **Pros:** Simple.
- **Cons / why rejected:** Silent corruption of species–calculation associations. Untrustworthy ML datasets downstream.

### Alternative B: Warn on graph mismatch, never reject

- **Description:** Check graph isomorphism but only issue warnings, never block ingestion.
- **Pros:** Permissive. No false rejections.
- **Cons / why rejected:** For species minima, a graph mismatch means the calculation optimized to a *different molecule*. This is not a "warning" — it means the calculation does not validate the claimed species entry. Permissive behavior muddies chemical identity, which must stay sharp in TCKDB.

### Alternative C: Strict coordinate equality

- **Description:** Require the output geometry to be numerically close to the input geometry.
- **Pros:** Catches large structural changes.
- **Cons / why rejected:** Legitimate cases fail: bad initial guesses that relax correctly, conformer collapse, flexible chain folding, symmetry-related orientation changes. RMSD thresholds would need to be molecule-size-dependent and would still produce false rejections.

### Alternative D: Graph isomorphism as hard gate, RMSD as advisory (chosen)

- **Description:** Fail on graph mismatch (different molecule). Warn on high RMSD (large structural change within the same molecule). Pass otherwise.
- **Pros:** Catches real errors (wrong species) without rejecting valid conformer relaxation.
- **Cons:** Requires graph isomorphism infrastructure (already exists in TCKDB).

## Decision

For species-entry optimization uploads:

```
if not is_isomorphic:
    return "fail"       # different molecule — block acceptance
if rmsd > threshold:
    return "warning"    # same molecule, large structural change
return "pass"
```

- **Fail:** Final output geometry is not graph-isomorphic to the uploaded species identity. This blocks acceptance into the "validated supporting calculation" path.
- **Warning:** Graph identity matches but RMSD exceeds a configurable threshold (~1.0 Å for small/medium molecules). Useful metadata, does not reject.
- **Pass:** Graph identity matches, RMSD within normal range.

Results are stored in `calc_geometry_validation` (one row per calculation) with: `is_isomorphic`, `rmsd`, `atom_mapping`, `n_mappings`, `validation_status`, `validation_reason`, and the `rmsd_warning_threshold` used.

## Scientific Justification

Chemical identity in a molecular database is defined by the molecular graph (connectivity), not by 3D coordinates. Two conformers of ethanol are the same species; ethanol and dimethyl ether are not, even if their coordinates happen to be numerically similar.

Graph isomorphism is the correct mathematical test for "same molecule":
- It is invariant to atom ordering, rotation, translation, and coordinate representation.
- It catches proton transfers, bond rearrangements, dissociation, and wrong-species uploads.
- It allows legitimate conformational changes (torsion rotation, ring puckering) that do not alter connectivity.

RMSD after Kabsch alignment provides a *suspicion signal* but not an identity criterion. Large RMSD values may indicate:
- A bad initial guess that relaxed into a valid minimum (legitimate).
- Conformer collapse (legitimate).
- A near-dissociation geometry that remained connected (suspicious).

Since RMSD does not discriminate between legitimate and problematic cases, it serves as an advisory metric rather than a hard gate.

For transition states and scan/IRC intermediates, different validation policies will apply (future work). This decision covers species minimum optimizations only.

## Implementation Notes

- **Service:** `app/services/geometry_validation.py` — pure-computation function returning a `GeometryValidationResult` dataclass
- **ORM:** `CalculationGeometryValidation` in `app/db/models/calculation.py`
- **Dependencies:** Uses `resolve_atom_mapping()` from `app/chemistry/torsion_fingerprint.py` for graph isomorphism and `kabsch_rmsd()` for RMSD computation — both already existed for conformer grouping (DR-0005)
- **Enum:** `ValidationStatus` (`passed`, `warning`, `fail`) in `app/db/models/common.py`

## Limitations & Future Work

- Only species minimum optimizations are covered. Transition state validation will need a different policy (imaginary frequency check, connectivity at saddle point).
- The RMSD warning threshold is a single configurable float. Future work may make it molecule-size-dependent or use a per-atom metric.
- Connectivity inference from 3D coordinates uses distance-based bond detection, which can be unreliable for unusual bonding situations (metal complexes, hypervalent species). The SMILES-based molecular graph is the authoritative reference.
- The validation service does not currently block database insertion — it produces a result that the workflow layer stores. Enforcement policy (reject, quarantine, accept-with-flag) is a workflow-layer concern.

## References

- DR-0005: Conformer Group Assignment by Torsional Basin Matching (uses the same `resolve_atom_mapping()` and `kabsch_rmsd()` infrastructure)
- Kabsch, W. (1976). A solution for the best rotation to relate two sets of vectors. *Acta Crystallographica*, A32, 922–923.
