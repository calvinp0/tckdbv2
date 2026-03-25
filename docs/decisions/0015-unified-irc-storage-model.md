# DR-0015: Unified IRC Storage Model — Direction at Point Level

**Date:** 2026-03-25
**Status:** Accepted (supersedes DR-0010)
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

DR-0010 established the IRC result tables (`calc_irc_result`, `calc_irc_point`) under the assumption that one IRC log = one direction. This was correct for Gaussian, which produces separate output files for forward and reverse IRC directions.

Testing with ORCA IRC output revealed that ORCA supports `Direction both` — a single calculation that traces the IRC in both directions from the TS. The ORCA IRC PATH SUMMARY contains all points from both directions in a single ordered list, with the TS point marked `<= TS` in the middle.

The original schema stored direction only on `calc_irc_result` (the parent row), making it impossible to represent a single ORCA calculation containing both forward and reverse points.

## Considered Alternatives

### Alternative A: Force ORCA both-direction IRC into two separate calculation rows

- **Description:** Split the ORCA output at the TS point and create two `Calculation` rows (one forward, one reverse), mirroring the Gaussian convention.
- **Pros:** Keeps the original schema unchanged.
- **Cons / why rejected:** Violates the provenance rule: one output log = one calculation row. Splitting a single ORCA job into two calculation rows creates a false provenance trail. It also requires synthetic splitting logic in the parser, which introduces error and loses the information that ORCA ran both directions as a single optimization.

### Alternative B: Store direction at the point level (chosen)

- **Description:** Add `direction` (nullable) and `is_ts` (boolean) to `calc_irc_point`. Keep `direction` on `calc_irc_result` as the overall run mode (`forward`, `reverse`, or `both`). Add `has_forward`, `has_reverse`, and `ts_point_index` to `calc_irc_result`.
- **Pros:** One calculation row per log (honest provenance). Works for both Gaussian (all points same direction) and ORCA (points split by TS). The TS point has `direction = NULL` and `is_ts = true`. Point-level direction enables correct per-direction queries.
- **Cons:** Slightly more complex than the original single-direction model. Acceptable — the complexity reflects real-world data diversity.

## Decision

Move direction to the point level. The unified model:

- **Gaussian forward log:** `calc_irc_result.direction = forward`, all `calc_irc_point.direction = forward`, point 0 has `is_ts = true`.
- **Gaussian reverse log:** Same pattern with `reverse`.
- **ORCA both-directions log:** `calc_irc_result.direction = both`, points before TS have `direction = reverse`, the TS point has `direction = NULL, is_ts = true`, points after TS have `direction = forward`.

`point_index` preserves the source step number from the log file. No synthetic renumbering.

The `IRCDirection` enum gains a `both` value. `calc_irc_point.direction` reuses the same enum type (with `create_type=False` to share the PostgreSQL enum).

## Scientific Justification

An IRC traces the steepest-descent path from a transition state in mass-weighted coordinates. The path is inherently bidirectional — from the TS toward reactants and from the TS toward products. Whether the software produces one file or two is an implementation detail, not a scientific distinction.

Gaussian's convention of separate forward/reverse jobs reflects its architecture (Link system, checkpoint files). ORCA's convention of a single bidirectional job reflects its architecture (internal optimizer). Both produce the same scientific object: a discretized IRC path through the TS.

The storage model should reflect the scientific object (a path with two branches meeting at a saddle point), not the software's file organization. Storing direction per point achieves this: each point knows which branch it belongs to, and the TS point sits at the junction.

Preserving the source step index (rather than forcing TS = 0) is important for provenance. ORCA's step 74 being the TS is a real observation from the calculation — renumbering it to 0 would be a lossy transformation that obscures the actual path the optimizer followed.

## Implementation Notes

- `app/db/models/common.py`: `IRCDirection` enum gains `both` value.
- `app/db/models/calculation.py`: `CalculationIRCResult` adds `has_forward`, `has_reverse`, `ts_point_index`. `CalculationIRCPoint` adds `direction` (nullable, reuses `irc_direction` enum) and `is_ts` (boolean), plus `max_gradient` and `rms_gradient` for ORCA gradient data.
- `app/services/orca_parameter_parser.py`: `parse_irc_path_summary()` extracts from `IRC PATH SUMMARY`, detects `<= TS` marker, assigns per-point directions based on TS position, converts kcal/mol → kJ/mol.
- Migration: `calc_irc_result` and `calc_irc_point` updated in the initial migration. The `irc_direction` enum is shared between the result and point tables using `create_type=False`.

## Limitations & Future Work

- Gaussian IRC parser has not yet been updated to populate the new `direction` and `is_ts` fields at the point level. The schema supports it; the parser needs the corresponding logic.
- ORCA IRC direction assignment (steps before TS = reverse, after = forward) follows a reasonable convention but may need validation against ORCA's internal definition of forward/backward.
- Per-point geometry linkage (`geometry_id`) requires ingesting geometries from the IRC trajectory file, not the PATH SUMMARY.

## References

- Fukui, K. Acc. Chem. Res. 1981, 14, 363–368. (IRC theory)
- Hratchian, H. P.; Schlegel, H. B. J. Chem. Phys. 2004, 120, 9918–9924. (Gaussian IRC implementation)
- DR-0010: IRC Result Table Design (superseded — established the initial separate-table design)
- DR-0012: Cross-Software Parser Architecture
