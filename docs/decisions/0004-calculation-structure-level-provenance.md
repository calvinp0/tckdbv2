# DR-0004: Calculation Structure-Level Provenance

**Date:** 2026-03-22
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

A `calculation` row in TCKDB represents a single computational chemistry job (geometry optimization, frequency analysis, single-point energy evaluation, etc.). Prior to this decision, calculations were owned by a `species_entry` (chemical identity) or `transition_state_entry`, but had no formal link to the specific 3D structure (conformer) they were performed on.

This became a concrete problem when attaching DLPNO-CCSD(T)/cc-pVTZ single-point energies as source calculations for kinetics records. The SP calculation was placed on the correct `species_entry` (via SMILES deduplication), but there was no way to distinguish *which conformer's geometry* the SP was run on — critical when multiple users upload different conformers of the same species.

In computational chemistry, the notation `DLPNO-CCSD(T)/cc-pVTZ//wB97X-D/def2-TZVP` encodes a chain of dependent computations: the SP energy was evaluated on a geometry optimized at a different level of theory. This is fundamentally a provenance DAG, not a flat property.

## Considered Alternatives

### Alternative A: Store composite LoT string on kinetics

- **Description:** Add a `level_of_theory` text field to the kinetics table (e.g., `"DLPNO-CCSD(T)/cc-pVTZ//wB97X-D/def2-TZVP"`).
- **Pros:** Simple, human-readable.
- **Cons / why rejected:** Flattens the provenance graph into a string. Not machine-queryable. Cannot distinguish which geometry the SP was run on. Violates the principle that LoT belongs to calculations, not to derived results.

### Alternative B: Species-entry-level attachment only

- **Description:** Attach SP calculations to the `species_entry` via `species_entry_id`. No conformer-level anchor.
- **Pros:** No schema change needed.
- **Cons / why rejected:** Ambiguous when a species has multiple conformers. Two users uploading different conformers of NH₃ with identical metadata would produce indistinguishable SP calculations. The structure context is lost.

### Alternative C: Full DAG-only model (no direct conformer link)

- **Description:** Rely entirely on `calculation_dependency` edges (SP → OPT → geometry) to recover the conformer lineage. No direct `conformer_observation_id` on `calculation`.
- **Pros:** Fully general. No redundant links.
- **Cons / why rejected:** Requires traversing the DAG to answer "which conformer does this SP belong to?" — expensive for queries and fragile if any edge is missing. The direct link complements the DAG; it doesn't replace it.

## Decision

Two complementary mechanisms:

1. **Direct conformer anchor:** Add a nullable `conformer_observation_id` FK on the `calculation` table. This provides O(1) lookup: "which conformer context does this calculation belong to?"

2. **Typed dependency edges:** Use the existing `calculation_dependency` table (with roles like `single_point_on`, `freq_on`) to record the computational lineage between calculations.

These are complementary, not redundant:
- `conformer_observation_id` = *"which structure bucket does this calc belong to?"* (grouping)
- `calculation_dependency` = *"which exact upstream calculation did it derive from?"* (provenance)

## Scientific Justification

In computational thermochemistry and kinetics, a single scientific result (e.g., an Arrhenius rate expression) depends on a DAG of computations:

```
opt (wB97X-D/def2-TZVP) → geometry
  ├── freq (wB97X-D/def2-TZVP) → ZPE, partition functions
  └── SP (DLPNO-CCSD(T)/cc-pVTZ) → electronic energy
                                         ↓
                                    Arkane fitting → k(T)
```

The composite level of theory `DLPNO-CCSD(T)/cc-pVTZ//wB97X-D/def2-TZVP` is **derived from traversing this graph**, not stored as a property of the kinetics record. This is consistent with how computational chemistry metadata is tracked in programs like Arkane, Gaussian, and ORCA — the method/basis is a property of each job, and composite protocols emerge from the job chain.

The conformer anchor ensures that when multiple conformers exist for the same species identity, each calculation is unambiguously associated with the specific 3D structure it was performed on. This is essential for conformer-resolved thermochemistry and for reproducing published computational results.

## Implementation Notes

- `app/db/models/calculation.py`: Added `conformer_observation_id` (nullable FK to `conformer_observation`).
- `app/db/models/species.py`: Disambiguated `ConformerObservation.calculation` relationship with explicit `foreign_keys`.
- `app/workflows/conformer.py`: After creating the observation, sets `calculation.conformer_observation_id = observation.id` on the primary opt calculation.
- `app/schemas/workflows/kinetics_upload.py`: Added `KineticsSourceCalculationUpload` with optional `conformer_label` field. When provided, the workflow resolves the conformer observation and anchors the source calculation.
- `app/workflows/kinetics.py`: Resolves conformer label → observation, sets `conformer_observation_id` on source calculations.
- Migration: `d861dfd60891` updated with the new column and deferred FK constraint.

## Limitations & Future Work

- **TS calculations** do not yet have a conformer-level anchor (transition states have a different structure model). A similar mechanism may be needed for TS entries.
- **Calculation dependency edges** (SP → OPT) are not yet automatically created by the kinetics source calculation upload. The kinetics workflow creates the SP and anchors it to the conformer, but the `single_point_on` edge to the upstream OPT requires knowing the opt calculation ID — future work.
- **Multi-conformer resolution** in the kinetics upload requires the user to supply `conformer_label`. An alternative would be auto-resolving to the default/preferred conformer when unambiguous.

## References

- DR-0003: Energy Correction Two-Layer Architecture (related provenance design)
- `calculation_dependency` table with roles: `single_point_on`, `freq_on`, `optimized_from`, etc.
- IUPAC recommendations on reporting computational chemistry methods (doi:10.1515/pac-2019-0603)
