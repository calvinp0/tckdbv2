# DR-0001: Pressure-Dependent Kinetics Architecture

**Date:** 2026-03-19
**Status:** Accepted
**Authors:** Calvin (domain lead), Claude (implementation)

## Context

TCKDB stores kinetics data for elementary chemical reactions. The existing `kinetics` table supports
high-pressure-limit (HPL) rate expressions — Arrhenius and modified Arrhenius — linked to individual
`reaction_entry` records via transition-state theory (TST). This is correct for pressure-independent,
elementary-step kinetics.

Pressure-dependent (PDep) kinetics arise from solving the master equation (ME) over a reaction network
containing multiple wells (intermediates) and channels. The output is a set of *phenomenological* rate
coefficients k(T, P) describing apparent macroscopic transformations (e.g., A + B → D) that may not
correspond one-to-one with any single elementary step. These phenomenological rates are emergent
properties of the network, not properties of individual reaction steps.

A common source of schema confusion is the conflation of three distinct layers:

1. **Microscopic kinetics** — k(T) for an elementary step via TST, pressure-independent.
2. **Well thermodynamics** — energies, densities of states, and partition functions for intermediates.
   These are inputs to the ME solver, not rate constants.
3. **Phenomenological kinetics** — k(T, P) produced by solving the ME over the full network.
   These belong to (source, sink) channels within the network, not to individual elementary steps.

Intermediates (wells) never have standalone rate constants in a pressure-dependent context; their
"effective" rates depend on the energy distribution, collisional environment, and pressure — i.e.,
on the full network solution.

## Considered Alternatives

### Alternative A: Extend the existing `kinetics` table with pressure-dependent fields

- **Description:** Add `pmin_bar`, `pmax_bar`, and model-specific columns (Chebyshev coefficients,
  PLOG entries, etc.) to the existing `kinetics` table. Add new values to `KineticsModelKind`.
  Phenomenological k(T, P) would be stored as `kinetics` rows linked to `reaction_entry`.
- **Pros:** Fewer tables; simpler initial migration.
- **Cons / why rejected:** Conflates two fundamentally different scientific objects. A phenomenological
  PDep channel is not the same as an elementary-step rate from TST. A PDep channel may collapse
  many micro paths, represent stabilization into a well, or describe net conversion between
  macroscopic states — none of which map cleanly to a single `reaction_entry`. This would also
  make the `kinetics` table increasingly sparse as different model kinds require different column
  sets. Rejected because it violates the identity-vs-result separation principle and would lead
  to semantic confusion.

### Alternative B: Hang `network_kinetics` directly off `network`, identify channels via `reaction_entry_id`

- **Description:** Create a `network_kinetics` table with FK to `network` and `reaction_entry`.
  Each row represents one phenomenological channel identified by the elementary reaction it
  most closely resembles.
- **Pros:** Reuses existing `reaction_entry` identity; avoids new tables for channel definition.
- **Cons / why rejected:** A phenomenological channel is not a microscopic reaction. Stabilization
  channels (A + B → C where C is a well) have no corresponding elementary `reaction_entry`.
  Overall pathways (A + B → D skipping intermediate C) may not correspond to any single TS.
  Forcing a mapping to `reaction_entry` would require creating artificial "pseudo" reaction entries,
  polluting the elementary-step layer. Rejected because it conflates microscopic and
  phenomenological identity.

### Alternative C: `network_state` → `network_channel` → `network_kinetics` (chosen)

- **Description:** Introduce three layers of abstraction within the network domain:
  - `network_state`: a macroscopic state in the network (well, bimolecular entrance, bimolecular exit)
  - `network_channel`: a directed (source_state → sink_state) pair representing one phenomenological pathway
  - `network_kinetics`: one fitted k(T, P) representation for a channel from a specific ME solve

  Separate `network` (abstract scientific object) from `network_solve` (one ME solution with
  specific method, bath gas, grain parameters, T/P range).
- **Pros:** Clean separation of identity, solve context, and fitted results. Uniform representation
  of wells and bimolecular states. Channels defined by network states, not elementary steps.
  Multiple solves per network supported naturally. Per-parameterization child tables keep the
  schema normalized and type-safe.
- **Cons:** More tables. Acceptable because each table has a clear, non-overlapping responsibility.

## Decision

Adopt **Alternative C**: the `network_state` → `network_channel` → `network_kinetics` architecture
with `network_solve` separating the abstract network from individual ME solutions.

### The mental model

```
network                = abstract set of wells + micro reactions
network_reaction       = the microscopic elementary steps admitted into the ME model
network_species        = flat membership / annotation (informational, not topology-defining)
network_state          = macroscopic chemically meaningful state (well, bimolecular, etc.)
network_channel        = directed macro transition between two states
network_solve          = one specific ME calculation / configuration / provenance
network_kinetics       = one fitted/exported k(T,P) for one channel under one solve
```

### New tables

| Table | Purpose |
|-------|---------|
| `network_state` | Macroscopic state with explicit `kind` and `composition_hash` |
| `network_state_participant` | Species composition of a network state |
| `network_channel` | Directed (source → sink) phenomenological pathway with explicit `kind` |
| `network_solve` | One ME solution: method, bath gas, grain params, T/P range, provenance |
| `network_solve_bath_gas` | Bath gas composition for a solve (species + mole fraction) |
| `network_solve_energy_transfer` | Energy transfer model parameters for a solve |
| `network_solve_source_calculation` | Links a solve to supporting calculations by role |
| `network_kinetics` | One fitted k(T, P) for a channel from a specific solve, with parent-level units/ranges |
| `network_kinetics_chebyshev` | Chebyshev polynomial coefficients (1:1 with parent) |
| `network_kinetics_plog` | PLOG entries — Arrhenius params at discrete pressures |
| `network_kinetics_point` | Tabulated k(T, P) grid points |

### What stays unchanged

- `kinetics` table: continues to store HPL k(T) from TST, linked to `reaction_entry`.
- `network`, `network_reaction`: existing tables remain as-is.
- `network_species`: stays for flat membership queries and role tagging, but does **not** define
  source/sink topology. That role belongs exclusively to `network_state` / `network_state_participant`.

### New enums

- `NetworkKineticsModelKind`: `chebyshev`, `plog`, `tabulated` (MVP); `falloff_lindemann`,
  `falloff_troe`, `falloff_sri` deferred.
- `NetworkStateKind`: `well`, `bimolecular`, `termolecular`.
- `NetworkChannelKind`: `isomerization`, `association`, `dissociation`, `stabilization`, `exchange`.
- `NetworkSolveCalculationRole`: `well_energy`, `barrier_energy`, `well_freq`, `barrier_freq`,
  `master_equation_run`, `fit_source` (ME-specific, not reusing `KineticsCalculationRole`).

### Key constraints and invariants

1. **`network_state.composition_hash`** — Canonical hash computed from sorted
   `(species_entry_id, stoichiometry)` pairs. Unique on `(network_id, composition_hash)`.
   Prevents duplicate states like "A + B" vs "B + A" appearing as separate rows.

2. **`network_state.kind`** — Explicit enum (`well`, `bimolecular`, `termolecular`). Avoids
   requiring queries to infer state type from participant count and stoichiometry.

3. **`network_channel` is directional** — `source_state_id` and `sink_state_id` are ordered.
   A + B → C and C → A + B are two distinct channel rows, because the forward and reverse
   phenomenological fits are separately addressable. Unique on
   `(network_id, source_state_id, sink_state_id)`.

4. **`network_channel.kind`** — Explicit classifier (e.g., `isomerization`, `stabilization`).
   Derivable from state kinds in principle, but stored explicitly for UI, export, validation,
   and querying convenience.

5. **`network_kinetics` points to both `network_channel` and `network_solve`** — One channel can
   have different fitted representations under different solves. This three-way split
   (channel × solve × fit) is the core of the design.

6. **Parent-level metadata on `network_kinetics`** — `tmin_k`, `tmax_k`, `pmin_bar`, `pmax_bar`,
   `rate_units`, `pressure_units`, `temperature_units` live on `network_kinetics`, not repeated
   per child row. For Chebyshev, these are also the normalization bounds. An optional
   `stores_log10_k` boolean for tabulated data.

7. **`network_solve` is the provenance anchor** — Carries `literature_id`, `software_release_id`,
   `workflow_tool_release_id`, ME method, interpolation settings, bath gas composition, energy
   transfer model, grain settings, and T/P range. Follows the same provenance pattern as
   `kinetics`, `thermo`, and `statmech`.

8. **`network_solve_source_calculation`** — Links to supporting calculations by role, using a
   dedicated `NetworkSolveCalculationRole` enum (not reusing `KineticsCalculationRole`, which
   is too reaction-kinetics-specific).

9. **No FK from `network_channel` to `reaction_entry`** — Phenomenological channels are not
   microscopic reaction steps. `network_reaction` links micro steps to the network (ME inputs);
   `network_channel` describes macro outputs. These are distinct layers that must not be
   conflated.

10. **PLOG ordering** — `network_kinetics_plog` uses `(network_kinetics_id, pressure_bar,
    entry_index)` to accommodate formats where multiple Arrhenius expressions exist at the
    same pressure. For MVP, one row per pressure is expected, but the schema does not
    preclude duplicates.

## Scientific Justification

In RRKM/master-equation theory, the microcanonical rate coefficients k(E) for elementary steps
are combined with collisional energy transfer models and solved as a system of coupled differential
equations. The eigenvalues of the resulting matrix yield chemically significant eigenvalues (CSEs)
that correspond to phenomenological rate coefficients for macroscopic channels. These
phenomenological rates:

- Are functions of both temperature and pressure, k(T, P).
- Represent net flux between macroscopic states (wells or bimolecular asymptotes), not between
  individual molecular configurations.
- Cannot, in general, be decomposed back into contributions from individual elementary steps.
- Depend on the collisional environment (bath gas identity, energy transfer parameters).

This physics dictates the schema separation:

1. **Elementary k(T)** belongs to `reaction_entry → kinetics` because it is a property of one TS.
2. **Phenomenological k(T, P)** belongs to `network → network_solve → network_kinetics` because
   it is a property of the network solution.
3. **Wells** are network states with thermodynamic properties, not rate constants.

The `network_state` abstraction reflects the standard ME formulation where the state space consists
of wells (bound intermediates) and bimolecular channels (reactant/product asymptotes). Channels
in the phenomenological rate matrix connect pairs of these states.

Representing phenomenological results as projections of the network solution (rather than as
standalone rate expressions) preserves provenance: every k(T, P) traces back to a specific
network, solved with specific parameters, for a specific channel. This is critical for
reproducibility and for comparing results across different solve configurations.

The directional nature of channels matches the standard output format of ME solvers (e.g., Arkane,
MESS, PAPR), which report forward and reverse phenomenological rates separately. Storing them as
directed pairs avoids ambiguity when the forward and reverse fits have different valid ranges or
different parameterization formats.

## Implementation Notes

- New ORM models in `app/db/models/network.py` (or split into `network_pdep.py` if too large).
- New enums in `app/db/models/common.py`.
- Per-parameterization tables use a 1:1 FK to `network_kinetics.id`, enforced by the ORM.
- `network_solve` carries provenance fields following the same pattern as `kinetics`.
- `network_species` remains informational; authoritative bath gas composition for a solve lives
  in `network_solve_bath_gas`.
- `composition_hash` is computed at the application layer (workflow/resolution) before insert,
  using sorted `(species_entry_id, stoichiometry)` tuples.
- Upload schemas and workflows for PDep will be added in a subsequent phase.
- An optional `representation_role` field on `network_kinetics` (e.g., `solver_output`, `refit`,
  `exported_mechanism`, `display`) is deferred but the column can be added without migration
  issues.

## Limitations & Future Work

- **Falloff parameterizations** (Troe, Lindemann, SRI) are deferred. They are lower-dimensional
  approximations applicable to simpler systems and can be added as additional
  `NetworkKineticsModelKind` values and per-parameterization tables.
- **Channel-to-elementary-step mapping** is not modeled. While a phenomenological channel may
  correlate with an elementary step, the schema intentionally does not enforce this mapping.
  An optional annotation link table could be added later.
- **Network-state-level energies** (e.g., zero-point-corrected energies relative to a reference
  within the network) are not included in MVP. Energies live indirectly through species/TS
  calculations and statmech/thermo provenance. A `network_state_energy` table could be added
  later for direct energy landscape inspection.
- **Multiple bath gas support** in a single solve is modeled via `network_solve_bath_gas`, but
  composition-dependent energy transfer parameters are stored as a single set per solve.
  Mixture rules are left to the application layer.
- **Uncertainty quantification** for fitted k(T, P) is not included in MVP.
- **Representation role** on `network_kinetics` (solver_output vs refit vs exported_mechanism)
  is useful but deferred.

## References

- J. W. Allen, C. F. Goldsmith, W. H. Green, "Automatic estimation of pressure-dependent rate
  coefficients," *Phys. Chem. Chem. Phys.*, 2012, 14, 1131–1155.
  DOI: [10.1039/C1CP22765C](https://doi.org/10.1039/C1CP22765C)
- RMG/Arkane documentation on pressure-dependent networks.
- TCKDB schema_spec.md and schema_analysis.md (internal).
