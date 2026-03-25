# DR-0011: Scan and IRC Result Extraction Architecture

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

ESS output logs for scans and IRCs contain three categories of information:

1. **Execution parameters** — how the job was configured (route-line keywords, convergence settings, resource allocations).
2. **Coordinate definitions** — what was scanned or followed (ModRedundant block for scans, IRC direction and step parameters).
3. **Path results** — what the calculation produced (per-point energies, geometries, reaction coordinates).

These categories map to different schema layers and require different parsing strategies. The question is how to architect the extraction pipeline so each layer is independent, robust, and cross-checkable.

## Considered Alternatives

### Alternative A: Single monolithic parser per log type

- **Description:** One function reads the entire log and populates all schema layers at once.
- **Pros:** Simple to invoke.
- **Cons / why rejected:** Couples unrelated concerns. A failure in geometry extraction would block parameter extraction. Hard to test, hard to evolve independently. Different layers have different failure modes and different tolerance for incompleteness.

### Alternative B: Layered extraction with independent parsers (chosen)

- **Description:** Separate parsers for each layer, each targeting its natural schema destination. Layers can succeed or fail independently.
- **Pros:** Clean separation of concerns. Each layer is independently testable. Archive-line fast-path can complement slower structured parsing. Cross-checking between layers catches inconsistencies.
- **Cons:** More functions to maintain. Coordination logic needed in the workflow layer.

## Decision

**Three independent extraction layers, each with a clear target:**

| Extraction layer | Source in log | Schema target | Parser function |
|-----------------|--------------|---------------|-----------------|
| **Execution parameters** | Route line, Link0 directives | `calculation_parameter` | `_parse_route_tokens()`, `_extract_link0()` |
| **Coordinate definition** | ModRedundant block (scan), IRC general parameters | `calc_scan_coordinate` / `calc_irc_result` | Dedicated parsers (scan: ModRedundant; IRC: from route + L123 block) |
| **Path results** | Per-point SCF energies, optimized geometries, archive line | `calc_scan_point` / `calc_irc_point` | Per-point extraction + archive-line fast-path |

**Archive-line strategy for scan energy extraction:**

Gaussian scan logs include an archive block at the end containing all scan-point energies in a compact `HF=E1,E2,...,EN` format. This is used as a fast-path extractor with cross-checking:

1. Parse the archive line for energies — fast, compact, reliable when present.
2. Cross-check: number of energies matches expected point count from ModRedundant definition.
3. If archive extraction fails or mismatches, fall back to slower per-point parsing (hunting `SCF Done` lines matched to `Stationary point found` markers).
4. Per-point geometries are always extracted from the structured log (the archive line does not contain geometries).

**Key principle:** The `modredundant=true` parameter in `calculation_parameter` signals "this is a scan" but does not define the scan coordinate. The actual scan definition (`D 2 3 4 5 S 45 8.0000`) lives in `calc_scan_coordinate`. This is the correct boundary: parameters tell you *how* the calculation was configured; result tables tell you *what* it produced.

## Scientific Justification

The layered architecture reflects a fundamental distinction in computational chemistry provenance:

- **Configuration provenance** answers: "What settings were chosen?" This is the domain of `calculation_parameter`. It is software-syntax-level information (route-line tokens, keyword flags).
- **Coordinate provenance** answers: "What physical degree of freedom was explored?" This is the domain of `calc_scan_coordinate` (atoms, step size, resolution) or `calc_irc_result` (direction, point count). It is chemically meaningful — a dihedral scan of atoms 2-3-4-5 at 8° resolution.
- **Result provenance** answers: "What did the calculation produce?" This is the domain of `calc_scan_point` / `calc_irc_point` (energies, geometries). It is observational data.

These three layers have different lifetimes and different trust levels:
- Configuration is immutable once the job runs.
- Coordinate definitions are immutable once specified.
- Results may be re-extracted if parsers improve (hence `parameters_parser_version`).

The archive-line fast-path is justified by the practical observation that Gaussian scan logs can be 60,000+ lines, but the archive block compresses all energies into ~10 lines. For a 46-point scan, parsing 46 `SCF Done` lines scattered across 66,000 lines is O(N) in file size; parsing the archive block is O(1). The cross-check catches archive corruption or parser bugs.

## Implementation Notes

- **Route-line parser:** Already implemented (`gaussian_parameter_parser.py`). Extracts `modredundant=true` under `section=opt` with `canonical_key=None`.
- **ModRedundant parser:** Extracts from the `The following ModRedundant input section has been read:` marker. Format: `{type} {atom1} {atom2} [{atom3} [{atom4}]] S {nsteps} {stepsize}`. Type is D(ihedral), A(ngle), or B(ond).
- **Archive-line parser:** Extracts from `\HF=E1,E2,...,EN\` in the Gaussian archive block (last ~30 lines of a normally terminated log). Line-wrapped, fields separated by `\`.
- **Schema targets:** `calc_scan_coordinate` (atoms, resolution), `calc_scan_result` (dimension, is_relaxed), `calc_scan_point` (energy, geometry_id)
- **IRC parallel:** Same layered approach. Route-line parser extracts `CalcAll`, `maxpoints`, `stepsize`, `forward`/`reverse` under `section=irc`. IRC point extraction targets `calc_irc_point`.

## Limitations & Future Work

- ModRedundant parser handles only `S` (scan) actions. Other ModRedundant actions (freeze `F`, add/remove bonds `B`/`A`) are not yet parsed.
- Archive-line parsing is Gaussian-specific. ORCA does not produce an equivalent compact summary. ORCA scan extraction will rely on structured output parsing only.
- Per-point geometry extraction from scan logs is not yet implemented. The archive line provides energies but not geometries.
- Multi-dimensional scans (2D, 3D) are supported by the schema (`calc_scan_result.dimension`, multiple `calc_scan_coordinate` rows) but not yet by the parser.

## References

- DR-0006: Three-Layer Calculation Parameter Architecture
- DR-0007: Parameter Observations, Not Possibilities
- DR-0010: IRC Result Table Design (parallel structure for IRC)
