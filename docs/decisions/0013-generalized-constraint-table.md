# DR-0013: Generalized Constraint Table — From Scan-Specific to Calculation-Level

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

The original schema included `calc_scan_constraint` — a table storing geometric constraints specifically attached to scan calculations. This assumed constraints were only relevant in the context of scans (e.g., holding a bond fixed while scanning a dihedral).

Testing with ORCA output files revealed that geometric constraints appear in multiple calculation types:
- **Constrained optimizations:** ORCA `%GEOM Constraints {C 0 C} ... END` freezes Cartesian coordinates of specific atoms during geometry optimization.
- **Constrained TS searches:** Same mechanism, different calculation type.
- **Scan-held constraints:** The original use case — coordinates frozen during a relaxed scan.
- **Constrained IRC setups:** Potential future use.

Additionally, the original table assumed all constraints reference internal coordinates (bond, angle, dihedral, improper) with 2–4 atoms. ORCA's Cartesian freeze (`{C 0 C}`) references a single atom, which did not fit the schema.

## Considered Alternatives

### Alternative A: Keep `calc_scan_constraint`, add a separate `calc_opt_constraint`

- **Description:** Create a parallel constraint table for each calculation type that uses constraints.
- **Pros:** Each table is specific to its context.
- **Cons / why rejected:** Constraints are structurally identical across calculation types — same atom references, same kind enum, same target values. Duplicating the table creates maintenance burden and fragments constraint queries.

### Alternative B: Generalize `calc_scan_constraint` into `calculation_constraint` (chosen)

- **Description:** Rename the table to `calculation_constraint`, attach it to `Calculation` (not `CalculationScanResult`), expand the constraint kind enum to include `cartesian_atom`, and make `atom2_index` nullable for single-atom constraints.
- **Pros:** One table serves all calculation types. Variable-arity support handles both internal coordinates and Cartesian freezes. Clean FK to `Calculation` means constraints are accessible regardless of calculation type.
- **Cons:** Slightly more complex arity check constraint. Acceptable — the CASE expression is clear and self-documenting.

## Decision

Rename `calc_scan_constraint` to `calculation_constraint`. Expand the `ConstraintKind` enum to include `cartesian_atom`. Make `atom2_index` nullable. Add a DB-level check constraint enforcing arity by kind. Attach the relationship to `Calculation`, not `CalculationScanResult`.

Keep `calculation_constraint` and `calc_scan_coordinate` as **separate tables**. Despite structural similarity (both reference atom tuples), they serve different semantic roles:
- **Constraint:** a coordinate held fixed during the calculation
- **Scan coordinate:** a coordinate intentionally stepped across values

Merging them would conflate "what is held still" with "what is varied."

## Scientific Justification

Geometric constraints are a general feature of computational chemistry workflows, not specific to potential energy surface scans. Constrained optimization is routinely used to:
- Relax a molecule while preserving specific structural features (e.g., freezing a reactive center to study peripheral relaxation)
- Generate starting geometries for transition state searches by constraining the reaction coordinate
- Explore conformational space with fixed backbone coordinates

ORCA's Cartesian freeze constraint (`{C N C}` — freeze all Cartesian coordinates of atom N) is a fundamentally different type from internal coordinate constraints. It references one atom, not an atom pair/triple/quadruple. A schema that forces all constraints into 2–4 atom tuples cannot represent this without distortion.

The variable-arity design (1 atom for Cartesian, 2 for bond, 3 for angle, 4 for dihedral/improper) mirrors how computational chemistry software actually defines constraints. It is the minimal schema that correctly represents the constraint space.

## Implementation Notes

- `app/db/models/common.py`: `ScanConstraintKind` renamed to `ConstraintKind`, with `cartesian_atom` added.
- `app/db/models/calculation.py`: `CalculationScanConstraint` renamed to `CalculationConstraint`. `atom2_index` made nullable. CASE check constraint enforces arity per kind. Relationship moved from `scan_constraints` to `constraints` on `Calculation`.
- `alembic/versions/d861dfd60891`: Table renamed from `calc_scan_constraint` to `calculation_constraint`.
- Parser: ORCA `%GEOM Constraints...END` content is correctly skipped (not stored as parameters). Constraint parsing for DB population is a future service-layer task.

## Limitations & Future Work

- The parser currently skips constraint content (`{C 0 C}` lines). A future constraint parser would extract these into `calculation_constraint` rows.
- `constraint_value` and `constraint_unit` fields may be needed for constraints with explicit target values (e.g., Gaussian's `B 1 2 F 1.5` — fix bond at 1.5 Angstrom).
- Cartesian axis-specific freezes (`{C 0 X}`, `{C 0 Y}`) are not yet modeled. The `cartesian_atom` kind freezes all three axes. Axis-specific kinds can be added when real data requires them.

## References

- DR-0011: Scan and IRC Result Extraction Architecture
- DR-0012: Cross-Software Parser Architecture
