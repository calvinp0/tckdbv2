# DR-0014: NEB Image Result Design — Path Images vs Optimized TS

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

Nudged Elastic Band (NEB) calculations produce a discretized reaction path between reactant and product geometries. ORCA supports three NEB variants: NEB (plain), NEB-CI (climbing image), and NEB-TS (climbing image + saddle-point refinement). Each produces:

1. **Path images** — ordered geometries along the minimum energy path (0..N)
2. **Per-image energies and forces** — from the converged PATH SUMMARY
3. **A climbing image (CI)** — the highest-energy path image, promoted during optimization
4. **An optimized TS** (NEB-TS only) — a refined saddle point seeded from the CI

The question is how to store NEB results: what goes in a dedicated NEB table, what uses existing geometry infrastructure, and how to handle the TS refinement output.

ORCA NEB output also varies in format between NEB-CI (6-column PATH SUMMARY with path distances) and NEB-TS (5-column PATH SUMMARY without path distances, plus a separate TS row).

## Considered Alternatives

### Alternative A: Store everything in one table including the TS row

- **Description:** `calc_neb_image_result` stores all images plus the optimized TS with `image_index = -1` as a sentinel.
- **Pros:** Single table for all NEB output data.
- **Cons / why rejected:** The optimized TS is not a path image — it is a separately refined saddle point. Mixing it with images complicates queries ("show all NEB images" requires `image_index >= 0`; "highest-energy image" is different from "optimized TS"). A sentinel value is a sign the row belongs to a different concept.

### Alternative B: Separate path images from TS refinement (chosen)

- **Description:** `calc_neb_image_result` stores only real path images (0..N). The `is_climbing_image` flag marks the CI. The separately optimized TS (from NEB-TS) is stored through normal calculation output handling — as the calculation's refined TS geometry, potentially linked to a `transition_state_entry`.
- **Pros:** Clean separation of concepts. Queries are simple. The CI (a path sample) and the TS (a refined saddle point) maintain distinct identities. Image indexing is honest (0..N, no sentinels).
- **Cons:** The TS energy from the PATH SUMMARY is not stored in the NEB table. Acceptable — it belongs to the TS output, not the NEB path.

### Alternative C: No dedicated table; store only geometries

- **Description:** Store NEB images only as `calculation_output_geometry(role='neb_image')` with no per-image energy data.
- **Pros:** No new table.
- **Cons / why rejected:** Loses the energy profile, path distances, force residuals, and CI marker — the most scientifically valuable NEB output. Geometries alone cannot reconstruct the barrier shape.

## Decision

Create `calc_neb_image_result` with composite PK `(calculation_id, image_index)` for path images only. Store `is_climbing_image` as a boolean flag. Exclude the NEB-TS optimized TS row from this table.

Tier 1 geometry storage uses the existing `calculation_output_geometry(role='neb_image', output_order=0..N)` infrastructure.

The parser uses `rfind` to locate the **last** PATH SUMMARY block (the converged result), handles both NEB-CI (6-column with path distance) and NEB-TS (5-column without path distance) formats, and converts ORCA's kcal/mol relative energies to kJ/mol at the parser boundary.

## Scientific Justification

In NEB theory, the discretized path images are approximate representations of the minimum energy path (MEP). They are not stationary points — they are optimized under the constraint of elastic band forces connecting adjacent images. The climbing image is still a path image; it is simply optimized without the spring force along the tangent, allowing it to climb to the highest energy along the band.

The NEB-TS refinement is a fundamentally different operation: it takes the CI geometry as a starting guess and performs a full saddle-point optimization using eigenvector-following methods. The resulting TS geometry is a true first-order saddle point (one imaginary frequency), while the CI is merely an approximation constrained to the band.

Storing both in the same table conflates an approximate path sample with a refined stationary point. From a database perspective, the TS produced by NEB-TS has the same status as a TS found by any other method (OptTS, scan+opt, etc.) and should be stored equivalently.

The `is_climbing_image` flag preserves the algorithm's internal state — which image was promoted — without implying that image is a true saddle point. This is scientifically honest: the CI is a useful TS *estimate*, not a validated TS.

## Implementation Notes

- `app/db/models/calculation.py`: `CalculationNEBImageResult` with `image_index`, `electronic_energy_hartree`, `relative_energy_kj_mol`, `path_distance_angstrom`, `max_force`, `rms_force`, `is_climbing_image`.
- `app/services/orca_parameter_parser.py`: `parse_neb_path_summary()` extracts from both NEB-CI and NEB-TS PATH SUMMARY formats. Uses `rfind` for last summary. Skips `TS` rows. Converts kcal/mol → kJ/mol.
- Tested against three ORCA NEB variants: NEB-CI+LBFGS, NEB-TS+FIRE, NEB-TS+LBFGS.

## Limitations & Future Work

- Per-image geometry storage (Tier 1) requires ingesting the `orca_MEP_trj.xyz` artifact file, which is separate from the log parser.
- Tier 3 endpoint provenance (linking NEB endpoints to their source optimization calculations) uses existing `calculation_dependency` infrastructure but is not yet implemented.
- The NEB-TS optimized TS geometry needs a service-layer pathway for ingestion as a standard TS result.
- ORCA NEB-TS PATH SUMMARY omits path distances; these could potentially be reconstructed from image geometries if needed.

## References

- Henkelman, G.; Uberuaga, B. P.; Jónsson, H. J. Chem. Phys. 2000, 113, 9901–9904. (NEB method)
- Henkelman, G.; Jónsson, H. J. Chem. Phys. 2000, 113, 9978–9985. (Climbing image NEB)
- DR-0010: IRC Result Table Design
- DR-0011: Scan and IRC Result Extraction Architecture
- DR-0012: Cross-Software Parser Architecture
