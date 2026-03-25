# DR-0006: Three-Layer Calculation Parameter Architecture

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

Electronic structure software (ESS) calculations are controlled by numerous parameters: SCF convergence thresholds, integration grid quality, optimization algorithms, initial Hessian strategies, resource allocations, and many others. These execution-control settings are critical for reproducibility and for answering queries like "find all calculations that used tight SCF convergence."

Prior to this decision, TCKDB had two places for such information:

1. `level_of_theory.keywords` — a free-text field intended for chemically meaningful qualifiers but often used as a dump for route-line clutter.
2. `calculation_artifact` — raw input/output files, which preserve everything but are not queryable.

Neither was suitable. The keywords field conflated model chemistry (scientific identity) with execution control (run semantics). Artifacts are verbatim but opaque to SQL queries.

The core challenge: ESS parameters vary wildly across software packages (Gaussian, ORCA, Molpro, etc.), evolve with software versions, and include a mix of scientifically meaningful settings (grid quality, convergence criteria) and purely operational ones (memory, processor count). A fixed-column schema would require migrations for every new parameter; a pure JSONB blob would sacrifice queryability.

## Considered Alternatives

### Alternative A: Expand level_of_theory with more columns

- **Description:** Add `scf_convergence`, `grid_quality`, `opt_convergence`, etc. as columns on `level_of_theory`.
- **Pros:** Strongly typed, queryable, simple joins.
- **Cons / why rejected:** Conflates scientific model chemistry (what the LoT *is*) with execution control (how the job *ran*). Requires schema migration for every new parameter. Cannot represent software-specific or exotic parameters. Would bloat the LoT identity hash, causing calculations with identical model chemistry but different convergence settings to appear as different LoT rows.

### Alternative B: JSONB-only storage on calculation

- **Description:** Store all parsed parameters in a single `parameters_json` JSONB column on `calculation`.
- **Pros:** Flexible, no schema changes needed, human-inspectable.
- **Cons / why rejected:** JSONB queries are slower than indexed columns. Cannot enforce FK relationships for canonical ontology. No structured validation. Adequate as a snapshot but insufficient as the primary query surface.

### Alternative C: EAV parameter table with JSONB complement (chosen)

- **Description:** An Entity-Attribute-Value `calculation_parameter` table with both raw and canonical key/value pairs, complemented by a JSONB snapshot on `calculation` and raw artifacts.
- **Pros:** Handles arbitrary parameters without migrations. Queryable via indexed columns. Supports incremental canonicalization. JSONB provides fast bulk access.
- **Cons:** EAV queries can be verbose. Requires careful index design.

## Decision

Three complementary layers, each serving a distinct purpose:

1. **`calculation_artifact`** — raw file truth. The verbatim input/output files. Immutable provenance.
2. **`calculation.parameters_json`** — parsed snapshot. A JSONB blob produced by the parser. Fast for bulk access and human inspection. Versionable via `parameters_parser_version`.
3. **`calculation_parameter`** — indexed queryable slices. EAV rows with `(raw_key, raw_value)` for exact reproduction and `(canonical_key, canonical_value)` for cross-software queries. Nullable FK to `calculation_parameter_vocab` for ontology classification.

Additionally:

- `level_of_theory.keywords` retains its role but is narrowed to *chemically meaningful method qualifiers* (e.g., UKS, ROHF reference, F12 variant) — not execution-control syntax.
- `calculation.parameters_parser_version` and `parameters_extracted_at` track parser provenance so re-extraction is possible when parsers improve.

## Scientific Justification

In computational chemistry, the distinction between *model chemistry* and *execution control* is fundamental:

- **Model chemistry** (method, basis set, dispersion correction) defines *what* theoretical approximation is used. Two calculations at the same model chemistry should produce the same result in the complete-basis / converged-SCF limit.
- **Execution control** (convergence thresholds, grid quality, algorithm choices) defines *how* that model chemistry is realized computationally. Different execution settings can produce numerically different results even at the same model chemistry.

These must be stored separately because they answer different questions:
- "What level of theory was used?" → `level_of_theory`
- "How was the SCF converged?" → `calculation_parameter`
- "What did the actual input file look like?" → `calculation_artifact`

The EAV design with dual raw/canonical keys supports the reality that the same physical concept (e.g., "tight SCF convergence") has different syntactic representations across software (`tight` in Gaussian, `TightSCF` in ORCA). The `canonical_key` normalizes across software; the `raw_key` preserves exact software-specific syntax for reproduction.

The `calculation_parameter_vocab` table classifies parameters along dimensions critical for scientific database queries:
- `affects_scientific_result` — can materially change the computed value (grid quality, convergence criteria)
- `affects_numerics` — affects precision/convergence behavior
- `affects_resources` — purely operational (memory, processor count)

This classification enables queries like "find all scientifically equivalent calculations" by filtering on `affects_scientific_result = true` parameters only.

## Implementation Notes

- **ORM models:** `CalculationParameter`, `CalculationParameterVocab` in `app/db/models/calculation.py`
- **Indexes:** `(calculation_id)`, `(canonical_key)`, `(raw_key, section)`, `(canonical_key, canonical_value)` — covering the primary query patterns
- **Parser columns on `Calculation`:** `parameters_json` (JSONB), `parameters_parser_version` (text), `parameters_extracted_at` (timestamp)
- **Software identity:** Derived via `calculation → software_release → software`, not duplicated on parameter rows (DR-0006 drops the initially proposed `software_scope` column)
- **Section semantics:** `(section, raw_key)` is the raw semantic unit. The same `raw_key` (e.g., `tight`) in different sections (e.g., `opt` vs `scf`) maps to different canonical meanings.

## Limitations & Future Work

- The vocab table starts empty. Canonical keys are populated incrementally as parsers encounter and normalize parameters. Unmapped parameters (`canonical_key = NULL`) are stored and queryable by raw key.
- Value normalization (e.g., converting `32768mb` to bytes) is deferred to future work. Raw values are preserved as text.
- The `affects_scientific_result` flag is binary. Future work may introduce finer-grained classification (e.g., "affects within numerical noise" vs "affects qualitatively").

## References

- DR-0004: Calculation Structure-Level Provenance (conformer_observation_id, calculation DAG)
- Gaussian 09 User's Reference (route-line syntax)
- ORCA 5.0 Manual (keyword-line syntax)
