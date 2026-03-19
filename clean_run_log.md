# Clean Run Log

---

## 2026-03-19 — PDep Network Architecture (DR-0001)

**Backup:** `backup_tckdb_dev_2026-03-19.sql` (4044 lines)

### Table count
| | Before | After |
|---|---|---|
| Tables | 48 | 65 |
| New tables | — | 11 |
| Seed rows (reaction_family) | n/a (table missing) | 125 |

### New tables added

| Table | PK | Key constraints |
|-------|------|-----------------|
| `network_state` | `id` | unique `(network_id, composition_hash)` |
| `network_state_participant` | `(state_id, species_entry_id)` | `stoichiometry >= 1` |
| `network_channel` | `id` | unique `(network_id, source_state_id, sink_state_id)`, check `source ≠ sink` |
| `network_solve` | `id` | T/P range checks, `grain_count >= 1`, provenance FKs |
| `network_solve_bath_gas` | `(solve_id, species_entry_id)` | `0 < mole_fraction <= 1` |
| `network_solve_energy_transfer` | `id` | FK to `network_solve` |
| `network_solve_source_calculation` | `(solve_id, calculation_id, role)` | enum `network_solve_calc_role` |
| `network_kinetics` | `id` | T/P range checks, dual FK to channel + solve |
| `network_kinetics_chebyshev` | `network_kinetics_id` (1:1) | `n_temperature >= 1`, `n_pressure >= 1` |
| `network_kinetics_plog` | `(network_kinetics_id, pressure_bar, entry_index)` | `pressure > 0`, `entry_index >= 1` |
| `network_kinetics_point` | `(network_kinetics_id, temperature_k, pressure_bar)` | `T > 0`, `P > 0` |

### New enums added
- `network_state_kind`: `well`, `bimolecular`, `termolecular`
- `network_channel_kind`: `isomerization`, `association`, `dissociation`, `stabilization`, `exchange`
- `network_kinetics_model_kind`: `chebyshev`, `plog`, `tabulated`
- `network_solve_calc_role`: `well_energy`, `barrier_energy`, `well_freq`, `barrier_freq`, `master_equation_run`, `fit_source`

### Also present (not in previous DB state)
- `reaction_family` table now correctly created and seeded (125 rows) — was missing in previous DB state
- 6 additional scan-related tables (`calc_scan_*`) also appeared — likely from uncommitted model changes now picked up by `create_all`

### Tests
62 passed, 0 failed
