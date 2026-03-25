# DR-0016: Chemistry-First Lookup API

**Date:** 2026-03-26
**Status:** Accepted
**Authors:** Calvin

## Context

TCKDB stores computational chemistry data (species, calculations, thermo, kinetics) with strong identity separation: graph-level identity (`species`, `chem_reaction`) is distinct from structurally resolved entries (`species_entry`, `reaction_entry`), which in turn own calculations and properties.

External tools (ARC, RMG, Jupyter notebooks, web UIs, ML pipelines) need to query this data using chemical identifiers — SMILES, charge, multiplicity, level of theory — not database IDs.  The question is: what API shape serves all these clients without encoding any single tool's workflow assumptions?

Existing chemistry databases typically offer either flat search endpoints (returning everything loosely) or client-specific convenience APIs.  Neither approach scales well: flat search forces clients to filter and interpret results, while client-specific APIs create maintenance burden and coupling.

## Considered Alternatives

### Alternative A: Client-specific endpoints

- **Description:** Dedicated endpoints per tool, e.g., `/arc/check-species`, `/rmg/get-kinetics`.
- **Pros:** Optimized for each tool's specific workflow.
- **Cons / why rejected:** Creates N × M coupling between tools and endpoints.  New tools require new endpoints.  Embeds workflow assumptions in the server.

### Alternative B: Flat search with generic filters

- **Description:** Single `/search` endpoint with many optional query parameters returning raw DB objects.
- **Pros:** Simple to implement.
- **Cons / why rejected:** No match quality information.  Clients must parse raw results to determine if a match is exact or partial.  No clear contract about what "matched" means.

### Alternative C: Resource-oriented lookup with consistent envelope

- **Description:** Separate lookup endpoints organized by entity type (identity vs. result vs. composed), each returning a consistent `{query, match, results}` envelope with explicit match semantics.
- **Pros:** Client-agnostic.  Match quality is explicit.  Results are summary-oriented with links.  Extensible via `include` and `selection` parameters.
- **Cons:** Slightly more complex initial design.

## Decision

Adopt Alternative C: a chemistry-first, resource-oriented lookup API with a consistent response envelope.

The API is organized into three endpoint families:

1. **Identity lookup:** `/lookup/species`, `/lookup/reaction` — resolve chemical identity from SMILES/charge/multiplicity or reactant/product lists.
2. **Result lookup:** `/lookup/calculations`, `/lookup/thermo`, `/lookup/kinetics` — find results attached to a resolved entity, with level-of-theory filtering.
3. **Composed lookup:** `/lookup/species-calculation`, `/lookup/reaction-kinetics` — one-shot identity + result resolution to minimize round trips.

Every endpoint returns the same envelope:

```json
{
  "query": {"kind": "...", "inputs": {...}},
  "match": {"status": "exact|partial|none", "detail_codes": [...], "details": [...]},
  "results": [{"resource_type": "...", "id": N, "links": {...}, "summary": {...}}]
}
```

## Scientific Justification

Chemistry databases serve diverse consumers with fundamentally different workflows.  A rate constant from ARC is consumed by RMG for reactor modeling, by ML pipelines for feature extraction, and by humans for validation.  Encoding any single consumer's decision logic (e.g., "can ARC skip this calculation?") into the API creates fragile coupling.

The chosen design separates three concerns:

1. **What was asked** (`query`) — the chemical question in the caller's terms.
2. **How it was matched** (`match`) — explicit, machine-readable match quality so the caller can make informed decisions.
3. **What exists** (`results`) — summary-oriented data with links to canonical resources for full retrieval.

Match quality uses a three-axis internal taxonomy:
- **Identity:** exact / partial / none (grounded in InChI key for species, stoichiometry hash for reactions)
- **Result existence:** yes / no (calculation, thermo, kinetics)
- **Level of theory:** per-field (method, basis, dispersion, solvent) — exact / partial / none

This prevents ambiguity: a "partial" match always has `detail_codes` explaining what matched and what did not.

### Geometry as calculation result

Geometry is never treated as a species-level property.  It is always the output of a specific calculation at a specific level of theory.  The path is: species → species_entry → calculation (type=opt, converged) → geometry (role=final).  This is accessed via `include=geometry` on calculation-returning endpoints, not via a standalone geometry endpoint.

When `include=geometry` is requested but no geometry is available, the response returns `"geometry": null` with a `geometry_status` field explaining why (`not_applicable`, `missing`, or `incomplete`).

### Selection modes

When multiple calculations match (different conformers, repeated runs, different provenance), the default is to return all.  Clients may request deterministic single-result selection via measurable modes only:

- `selection=lowest_energy` — minimum electronic energy, tie-break: converged → newest → lowest calculation ID
- `selection=latest` — most recently created
- `selection=earliest` — oldest

Subjective selectors (`best`, `preferred`, `display_default`) are explicitly prohibited.  The test: two different people must compute the same winner from the same dataset.

### Reaction entry resolution

`/lookup/reaction` resolves to `reaction_entry` level, not just `chem_reaction` identity.  Each returned entry includes resolved participant structure (species_entry IDs, SMILES, role, ordered index) from `reaction_entry_structure_participant`.  This makes the response directly usable for kinetics, simulation, and ML without additional round trips.

## Implementation Notes

- All endpoints in `app/api/routes/lookup.py`, registered under `/api/v1/lookup/`.
- `_MatchBuilder` class accumulates `detail_codes` and derives the public `status`.
- `_apply_selection()` handles deterministic selection with the documented tie-breaker chain.
- `_reaction_entry_result()` builds participant structure summaries from `reaction_entry_structure_participant`.
- Tests in `tests/api/test_api_lookup.py` (33 tests covering all endpoints, match semantics, geometry expansion, and selection modes).

## Limitations & Future Work

- **Reaction lookup** does not yet support partial identity matching (e.g., one reactant found but not the other returning partial instead of none).
- **`include` parameter** currently supports only `geometry`.  Future expansions: `conformer`, `statmech`, `transport`.
- **`selection` parameter** is only on calculation-returning endpoints.  Could extend to thermo/kinetics if needed.
- **Rate of queries** is not throttled.  Production deployment will need rate limiting.
- **Caching** — lookup results are computed per-request.  Frequently queried species (e.g., H2, CH4) could benefit from response caching.

## References

- DR-0001: Pressure-Dependent Kinetics Architecture (network/reaction schema design)
- DR-0004: Calculation Structure-Level Provenance (calculation → geometry → species_entry chain)
