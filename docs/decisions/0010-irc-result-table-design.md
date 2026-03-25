# DR-0010: IRC Result Table Design — Separate Tables, One Log Per Calculation

**Date:** 2026-03-25
**Status:** Superseded by DR-0015
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

Intrinsic Reaction Coordinate (IRC) calculations trace the minimum-energy path from a transition state (TS) toward reactants (reverse) or products (forward). In practice, Gaussian produces separate output files for forward and reverse directions. TCKDB needs to store IRC path data: per-point energies, geometries, and reaction coordinates.

The existing scan result tables (`calc_scan_result`, `calc_scan_point`, `calc_scan_coordinate`) provide a structural precedent for storing ordered point data. The question is whether IRC should reuse, extend, or parallel the scan schema.

## Considered Alternatives

### Alternative A: Reuse scan tables for IRC

- **Description:** Store IRC points in `calc_scan_point` with an additional `is_irc` flag or a type discriminator.
- **Pros:** Less schema surface. Reuses existing infrastructure.
- **Cons / why rejected:** IRC and scan are semantically different objects. Scan samples a user-controlled coordinate; IRC follows a steepest-descent path from a saddle point. Scan uses `point_index >= 1`; IRC naturally has the TS at `point_index = 0`. Scan has explicit coordinate definitions (atoms, resolution); IRC has a reaction coordinate that emerges from the path. Forcing IRC into scan semantics would distort both.

### Alternative B: Single merged IRC calculation with negative/positive indices

- **Description:** One `Calculation` row represents the full forward+reverse IRC. Reverse points get negative indices; forward get positive. TS is point 0.
- **Pros:** Attractive for visualization. Single query for full path.
- **Cons / why rejected:** Negative indices are synthetic — they don't correspond to how Gaussian produced the data. Merging two separate output files into one calculation creates ambiguity about: which artifact belongs to which half, whether both directions actually ran, whether one direction used different settings, whether one branch should be reparsed independently.

### Alternative C: One log = one calculation, separate IRC tables (chosen)

- **Description:** Each IRC output file is its own `Calculation` row with its own `calc_irc_result` and `calc_irc_point` rows. The TS is point 0 in both. Direction is stored on the result row. Stitching the full path is a query-time concern.
- **Pros:** Honest to provenance (one artifact = one calculation). Clean separation. Each direction is independently uploadable, reproducible, and replaceable.
- **Cons:** Full path requires a join across two calculations. Slightly more complex queries.

## Decision

**Option C: One log = one calculation. Separate IRC tables parallel to (but not merged with) scan tables.**

Schema:

**`calc_irc_result`** — one row per IRC calculation:
- `calculation_id` (PK, FK → calculation)
- `direction` (NOT NULL: `forward` or `reverse`)
- `point_count`
- `zero_energy_reference_hartree` (TS energy for relative energies)

**`calc_irc_point`** — PK is `(calculation_id, point_index)`:
- `point_index` (>= 0, where 0 = TS)
- `reaction_coordinate` (cumulative, from `NET REACTION COORDINATE`)
- `electronic_energy_hartree`
- `relative_energy_kj_mol`
- `geometry_id` (FK → geometry)

Key design choices:
- `point_index = 0` is the TS. This is chemically natural for IRC; scan uses `>= 1`.
- `direction` is NOT NULL on the result (every IRC job knows its direction) but absent from the point table (redundant — inherited from parent).
- No `step_number` column — in Gaussian IRC output, step number and point index are always identical.

## Scientific Justification

An IRC calculation is a fundamentally different object from a scan:

- **Scan:** The user defines which internal coordinate to vary, the step size, and the number of steps. The path is user-controlled. The result is a potential energy surface slice along one (or more) chosen coordinates.
- **IRC:** The path is determined by the potential energy surface itself — it follows the steepest-descent (or mass-weighted steepest-descent) path from the transition state. The user controls only the integration parameters (step size, maximum points, Hessian strategy).

This semantic difference justifies separate tables. The moment `point_index = 0` has special meaning (the TS), the mismatch with scan's `point_index >= 1` convention becomes obvious.

The one-log-per-calculation principle follows from how IRC calculations are actually performed. In practice, forward and reverse directions are separate Gaussian jobs with separate output files, often submitted independently. They may:
- Use different step sizes or maximum points.
- Terminate at different numbers of steps.
- Be re-run independently if one direction fails.
- Be uploaded by different users or at different times.

Storing them as separate calculations preserves this provenance honestly. The full reaction path is reconstructed at query time by joining forward and reverse calculations that share the same transition state entry and level of theory.

## Implementation Notes

- **ORM models:** `CalculationIRCResult`, `CalculationIRCPoint` in `app/db/models/calculation.py`
- **Enum:** `IRCDirection` (`forward`, `reverse`) in `app/db/models/common.py`
- **Relationship on Calculation:** `irc_result` (uselist=False) and `irc_points` (ordered by point_index)
- **Existing CalculationType:** `irc` was already in the `CalculationType` enum; `irc_forward` and `irc_reverse` were already in `CalculationGeometryRole`
- **Parameter extraction:** The Gaussian parser extracts IRC route-line parameters (`CalcAll`, `maxpoints`, `stepsize`, `reverse`/`forward`) into `calculation_parameter` rows under `section=irc`. The generic `key=(sub-options)` handler works without IRC-specific code.

## Limitations & Future Work

- IRC result extraction (parsing per-point energies and geometries from the log) is not yet implemented. The tables and parameter extraction are in place.
- A lightweight grouping concept (e.g., `irc_pair_key` or shared `transition_state_entry_id`) could later link forward and reverse calculations explicitly. For now, pairing is inferred from shared TS, LoT, and metadata.
- ORCA IRC (or NEB) output has a different structure and will need a separate parser, but the same result tables should accommodate it.
- The `reaction_coordinate` column stores the cumulative path coordinate. Sign conventions (positive = forward, negative = reverse) are a query-layer concern, not a storage-layer concern.

## References

- Gonzalez, C.; Schlegel, H. B. (1990). Reaction path following in mass-weighted internal coordinates. *J. Phys. Chem.*, 94, 5523–5527.
- DR-0006: Three-Layer Calculation Parameter Architecture (parameter layer for IRC execution settings)
