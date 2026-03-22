# DR-0002: Transport Lennard-Jones Pair Validation

**Date:** 2026-03-20
**Status:** Accepted
**Authors:** Calvin (domain lead), Claude (implementation)

## Context

The `transport` table stores molecular transport properties for species entries, including
Lennard-Jones (LJ) parameters: collision diameter σ (`sigma_angstrom`) and well depth ε/k_B
(`epsilon_over_k_k`). These parameters are consumed by master-equation solvers for collisional
energy transfer calculations and by CHEMKIN-format mechanism exporters.

The question arose during schema design: should the upload API allow a transport record with
only one of the two LJ parameters populated? This is a tension between archival flexibility
(store whatever the literature reports) and operational correctness (downstream consumers
always need the complete pair).

## Considered Alternatives

### Alternative A: Loose (allow partial LJ data)

- **Description:** Allow `sigma_angstrom` and `epsilon_over_k_k` to be independently nullable.
  A record could have one without the other.
- **Pros:** More flexible for literature imports where a paper reports only one parameter.
  No data is rejected at upload time.
- **Cons / why rejected:** A transport record with only σ or only ε/k is operationally
  incomplete — no downstream consumer (Arkane, CHEMKIN, ME solver) can use half a
  Lennard-Jones pair. Storing it creates records that appear valid in the database but
  fail at solve time in a much less obvious place. Partial literature data is better
  captured as literature notes or a future "reported transport evidence" layer than as
  a half-populated transport row.

### Alternative B: Strict both-or-neither (chosen)

- **Description:** Enforce that `sigma_angstrom` and `epsilon_over_k_k` are either both
  provided or both omitted. Validation at both the Pydantic schema layer (for API requests)
  and the PostgreSQL layer (check constraint for any direct DB writes).
- **Pros:** Every stored transport record with LJ data is operationally complete. Upload-time
  errors are local and understandable. Defense-in-depth across two layers.
- **Cons:** Cannot store partial LJ data from literature. Accepted because partial data
  should use a different representation.

## Decision

Enforce **strict both-or-neither** for the Lennard-Jones parameter pair at create time:

- `TransportCreate` (Pydantic): `validate_lj_pair` rejects payloads where exactly one of
  σ or ε/k is provided.
- `transport` table (PostgreSQL): `lj_pair_both_or_neither` check constraint enforces the
  same invariant at the database level.
- `TransportUpdate` (PATCH): no LJ pair check, because a PATCH payload carries only the
  fields being changed. The pair invariant is evaluated after merging with the stored row,
  not on the partial patch alone.

## Scientific Justification

The Lennard-Jones 12-6 potential is defined as:

V(r) = 4ε[(σ/r)¹² − (σ/r)⁶]

Both parameters are required to specify the potential. In the context of TCKDB:

- **Master-equation solvers** (Arkane, MESS, PAPR) use LJ parameters to compute collisional
  energy transfer rates via the single-exponential-down model. The collision frequency
  calculation requires both σ and ε — one without the other is not physically meaningful.

- **CHEMKIN transport files** require all transport parameters as a complete record. A species
  with only σ would be rejected by any CHEMKIN-compatible solver.

- **Bath gas collision modeling** in the `network_solve_bath_gas` and
  `network_solve_energy_transfer` tables (DR-0001) depends on complete LJ parameters for
  each species involved.

A transport record is not an archival evidence table — it is a curated scientific product
that should be operationally complete when stored. Partial evidence from literature belongs
in the literature/provenance layer, not in a half-populated scientific product row.

## Implementation Notes

- Pydantic validation in `app/schemas/entities/transport.py`: `TransportCreate.validate_lj_pair`
- Database constraint in `app/db/models/transport.py`: `lj_pair_both_or_neither`
- `TransportUpdate` intentionally omits the pair check (PATCH semantics)

## Limitations & Future Work

- **Partial literature evidence**: If a future use case requires storing "paper X reported
  σ = 3.8 Å but did not report ε/k", this should be modeled as a separate evidence/extraction
  table rather than relaxing the transport record constraint.
- **Update-time validation**: The pair invariant after a PATCH merge is currently left to the
  database constraint. A service-layer merge-then-validate pattern could provide a friendlier
  error message.

## References

- DR-0001: Pressure-Dependent Kinetics Architecture (transport parameters used in ME solves)
- CHEMKIN transport data format specification
- R. J. Kee, G. Dixon-Lewis, J. Warnatz, M. E. Coltrin, J. A. Miller, "A Fortran Computer
  Code Package for the Evaluation of Gas-Phase, Multicomponent Transport Properties,"
  Sandia Report SAND86-8246, 1986.
