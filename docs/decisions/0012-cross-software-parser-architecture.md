# DR-0012: Cross-Software Parser Architecture — Unified Extraction with Software-Specific Parsers

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

TCKDB must ingest computational chemistry results from multiple electronic structure software packages (Gaussian, ORCA, and potentially others). Each package uses different input syntax, output formats, and conventions for representing the same scientific information: execution parameters, scan/IRC/NEB path results, software provenance, and molecular geometry.

The challenge is designing a parser architecture that:
- Handles each software's idiosyncratic output format faithfully
- Maps results into a single unified schema without losing provenance
- Keeps the canonical vocabulary consistent across software boundaries
- Normalizes units and indexing conventions at the parser boundary, not downstream

Key convention differences between Gaussian and ORCA include:
- **Atom indexing:** Gaussian uses 1-based; ORCA uses 0-based
- **Energy units:** Gaussian reports relative energies in various units; ORCA reports dE in kcal/mol
- **Block syntax:** Gaussian uses route-line `key=(sub,opts)`; ORCA uses `%block...END` with nested sub-blocks
- **IRC direction:** Gaussian produces one direction per log; ORCA supports both directions in one log
- **Scan definition:** Gaussian uses ModRedundant lines; ORCA uses `%GEOM SCAN` blocks
- **NEB results:** ORCA-specific (Gaussian does not have NEB)

## Considered Alternatives

### Alternative A: Single generic parser with software detection

- **Description:** One parser function that detects the software from the log header and branches internally.
- **Pros:** Single entry point; no code duplication.
- **Cons / why rejected:** The output formats are too different for a single parser to handle cleanly. Branching within one function leads to spaghetti code and makes each software path harder to test independently. Adding a new software package requires modifying the monolithic parser.

### Alternative B: Completely independent parsers with no shared vocabulary

- **Description:** Separate parsers per software, each returning its own ad hoc dict structure.
- **Pros:** Maximum flexibility per parser.
- **Cons / why rejected:** Without a shared canonical vocabulary, cross-software queries become impossible. "Find all calculations with tight SCF convergence" would require knowing every software's raw keyword variant. Schema mapping becomes duplicated across service layers.

### Alternative C: Software-specific parsers with shared canonical vocabulary (chosen)

- **Description:** Each software gets its own parser module (`gaussian_parameter_parser.py`, `orca_parameter_parser.py`) that returns dicts in a common structure. Both parsers share the same canonical key vocabulary (e.g., `scf_convergence`, `opt_convergence`, `grid_quality`) via their `_CANONICAL_MAP` lookup tables. Normalization (unit conversion, index adjustment) happens at the parser boundary.
- **Pros:** Clean separation of parsing concerns. Shared vocabulary enables cross-software queries. Each parser is independently testable. Adding a new software package means adding a new parser module without touching existing ones.
- **Cons:** Some vocabulary duplication across parser maps (acceptable — the maps are intentionally small and grow from observations).

## Decision

Adopt software-specific parser modules with a shared canonical vocabulary. Each parser:

1. **Extracts raw observations** from the log's native format, preserving `raw_key` and `raw_value` exactly as found.
2. **Maps to canonical keys** using a `(section, raw_key) → (canonical_key, canonical_value)` lookup. Unmapped parameters get `canonical_key = NULL` and are stored as raw observations for later normalization.
3. **Normalizes at the boundary:** ORCA 0-based atom indices → 1-based; kcal/mol → kJ/mol; trailing `END` stripped from block values. All downstream code sees only normalized values.
4. **Classifies keywords** into their correct schema destination: job types (→ `Calculation.type`), LoT keywords (→ `level_of_theory`), dispersion (→ `level_of_theory.dispersion`), execution parameters (→ `calculation_parameter`), scan definitions (→ `calc_scan_coordinate`), constraints (→ `calculation_constraint`).

## Scientific Justification

Computational chemistry software packages are not interchangeable in their output semantics. The same scientific concept (e.g., "tight SCF convergence") is expressed as `scf=(tight)` in Gaussian and `TightSCF` in ORCA, with potentially different numerical thresholds. A database that stores only raw keywords cannot answer cross-software scientific queries. A database that normalizes too aggressively loses provenance.

The two-layer key design (`raw_key` + `canonical_key`) preserves both: the raw key enables exact reproduction of the original input, while the canonical key enables cross-software comparison. This is analogous to how chemical databases store both SMILES (canonical) and original structure representations (provenance).

The `(section, raw_key)` compound lookup key is essential because the same raw keyword can have different meanings in different contexts. For example, `tight` in Gaussian's `opt=(tight)` means optimization convergence, while `tight` in `scf=(tight)` means SCF convergence. Without section context, canonicalization would be ambiguous.

Unit normalization at the parser boundary follows the principle that the database should use consistent canonical units throughout. ORCA reports IRC/NEB relative energies in kcal/mol, but TCKDB stores kJ/mol. Converting once at extraction time is cleaner and less error-prone than converting at every query.

## Implementation Notes

- `app/services/gaussian_parameter_parser.py` — Gaussian 09/16 log parser. Handles route-line tokenization, Link0 directives (with file-path exclusion), IOp blocks, ModRedundant scan definitions, and archive-line extraction.
- `app/services/orca_parameter_parser.py` — ORCA 5.x/6.x log parser. Handles `!` keyword lines (with inline `#` comment stripping), `%block...END` sections (with nested sub-block tracking for `%GEOM`), single-line vs multi-line block distinction, scan definitions (`%GEOM SCAN`), constraint skipping (`Constraints...END`), PATH SUMMARY extraction (NEB and IRC), and `<= CI`/`<= TS` marker detection.
- Both parsers return dicts with identical key structure: `raw_key`, `canonical_key`, `raw_value`, `canonical_value`, `section`, `value_type`.
- `_CANONICAL_MAP` in each parser uses the same canonical vocabulary. The vocabulary grows from parsed observations, not from pre-populating software manuals (see DR-0007).
- Scan coordinate extraction converts ORCA 0-based atom indices to 1-based at the parser boundary, with explicit documentation of this convention.

## Limitations & Future Work

- The canonical vocabulary is currently small (~20–40 keys). It will grow as more log files are parsed. The `calculation_parameter_vocab` table provides the ontology seed for future normalization.
- Parser version tracking (`parameters_parser_version` on `Calculation`) enables re-extraction when parsers improve.
- Additional software packages (Molpro, QChem, Psi4) would each need a new parser module following the same pattern.
- The `_looks_like_value` heuristic for ORCA single-line blocks is fragile for edge cases; the single-line vs multi-line distinction may need refinement as more block types are encountered.

## References

- DR-0006: Three-Layer Calculation Parameter Architecture
- DR-0007: Parameter Storage Rule — Observations, Not Possibilities
- DR-0008: Software Provenance Reconciliation
- DR-0010: IRC Result Table Design
- DR-0011: Scan and IRC Result Extraction Architecture
