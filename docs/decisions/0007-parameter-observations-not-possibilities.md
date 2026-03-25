# DR-0007: Parameter Storage Rule — Observations, Not Possibilities

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

Gaussian's `Opt` keyword alone supports dozens of sub-options spanning procedural options, Hessian strategies, convergence modes, algorithms, ONIOM controls, and coordinate-system choices. ORCA's keyword space is similarly large. The question arose: should the `calculation_parameter` table (DR-0006) be pre-populated with known parameters from software documentation, or should it only contain parameters actually encountered in parsed job files?

This decision has major implications for database size, query noise, and ontology maintenance burden.

## Considered Alternatives

### Alternative A: Pre-populate from software documentation

- **Description:** Seed the `calculation_parameter_vocab` table with every known parameter from Gaussian, ORCA, and other ESS manuals. Create parameter rows for default values even when not explicitly specified.
- **Pros:** Complete coverage. Enables queries about defaults.
- **Cons / why rejected:** Creates enormous noise. Most parameters are never explicitly set by users. Default values change across software versions. The database becomes a mirror of the Gaussian manual rather than a record of actual computations. Maintenance burden is extreme — every software update requires vocabulary updates.

### Alternative B: Store only parsed observations from actual jobs (chosen)

- **Description:** A parameter row is created only when a setting was explicitly present in the job input or clearly reported in the output. The vocab table grows organically from real data.
- **Pros:** Clean, honest, manageable. Database reflects actual practice. Vocabulary grows from evidence, not speculation.
- **Cons:** Some "interesting" defaults are not recorded. Queries about unset parameters return no rows rather than `value = default`.

## Decision

**Store only parsed observations from actual jobs.**

Three-tier classification for what to store:

1. **Core parameters** — store aggressively, always map to canonical keys. Examples: `scf_convergence`, `grid_quality`, `opt_convergence`, `initial_hessian`.
2. **Secondary parameters** — store if explicitly present in the input. Map to canonical keys if the parameter is common. Examples: `opt_max_cycles`, `scf_direct`, `eigen_test`.
3. **Exotic parameters** — store only if actually encountered. Leave `canonical_key = NULL`. Normalize later only if the parameter becomes important for queries. Examples: `IOp(2/9)`, `Mic103`, `QuadMacro`.

For each parsed option, the parser asks:
- Was it explicitly present in the job input? → Store it.
- Was it clearly reported in output and scientifically relevant? → Maybe store it.
- Is it just a documented possibility from the manual? → Do not store it.

## Scientific Justification

A thermochemical database records *what was computed*, not *what could be computed*. This parallels the species model in TCKDB: `species` rows represent observed chemical identities, not the space of all possible molecules. Similarly, `calculation_parameter` rows represent observed execution settings, not the space of all possible settings.

This principle prevents a category error: confusing the *ontology of possible parameters* (which belongs in documentation) with the *record of actual computations* (which belongs in the database). The vocab table serves as a lightweight ontology seed, but its growth is driven by real parsed data — not by importing the Gaussian User's Reference.

For exotic internal options (e.g., Gaussian's `IOp(2/9)=2000`), the raw key/value is preserved even when no canonical mapping exists. This ensures no information is lost, while avoiding the pretense of understanding options whose semantics may be undocumented or version-dependent.

## Implementation Notes

- **Parser rule:** The Gaussian and ORCA parsers only emit parameter rows for tokens actually present in the route line / keyword line and Link0 directives. They do not infer or emit defaults.
- **Vocab table:** `calculation_parameter_vocab` starts empty. Canonical keys are added as parsers are developed. Target: ~20–40 high-value keys initially across SCF, optimization, grid/integral, Hessian, coordinate system, guess/restart, and resource categories.
- **Nullable FK:** `calculation_parameter.canonical_key` is a nullable FK to `calculation_parameter_vocab.canonical_key`. Unmapped rows (`NULL`) store fine and are queryable by `(section, raw_key)`.
- **Link0 filtering:** File-path directives (`%chk`, `%oldchk`, `%rwf`) are excluded — they are not execution parameters. Resource directives (`%mem`, `%nprocshared`) are included.

## Limitations & Future Work

- Default values that materially affect results (e.g., Gaussian's default integration grid) are not recorded unless the program explicitly echoes them in output. Future parsers may selectively extract reported defaults from output sections.
- The three-tier classification (core / secondary / exotic) is a parser-design guideline, not a database constraint. The database stores all three identically.
- As the vocab grows, periodic review should identify frequently occurring `canonical_key = NULL` parameters that deserve normalization.

## References

- DR-0006: Three-Layer Calculation Parameter Architecture
- Gaussian 09 User's Reference (Opt keyword documentation — illustrates the scale of the option surface)
