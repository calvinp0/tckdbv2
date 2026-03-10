# TCKDB Schema Analysis

This document classifies each table by four questions:

- Identity: what the entity is
- Result: scientific/computational values produced about it
- Provenance: where it came from, who made it, what generated it
- Curation: chosen/preferred/status/quality fields

The goal is not to repeat SQL types or constraints. The goal is to make the semantic role of each field clear.

Migration details that materially affect semantics:

- `transition_state_entry.status` defaults to `optimized`
- `calculation.quality` defaults to `raw`
- `species.created_at`, `species_entry.created_at`, `chem_reaction.created_at`, `reaction_entry.created_at`, `transition_state.created_at`, `transition_state_entry.created_at`, `calculation.created_at`, `literature.created_at`, and `author.created_at` are `NOT NULL DEFAULT now()`
- `calculation.quality` uses the `calculation_quality` enum type
- `calculation_output_geometry.role` uses the `calc_geom_role` enum type
- `calculation_dependency.dependency_role` uses the `calc_dependency_role` enum type
- the calculation XOR ownership check is named `ck_calculation_exactly_one_owner`
- `kinetics.model_kind` defaults to `modified_arrhenius`
- `app_user.role` defaults to `user`
- `network_species.role` is nullable in the migration
- `reaction_entry.preferred_ts_entry_id` is an immediate FK, unlike the deferred preferred calculation pointers

## 1. species

### Identity

- `id`
- `kind`
- `smiles`
- `inchi_key`
- `charge`
- `multiplicity`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 2. species_entry

### Identity

- `id`
- `species_id`
- `kind`
- `mol`

### Result

- None

### Provenance

- `created_by`
- `created_at`

### Curation

- `preferred_calculation_id`

## 3. transport

### Identity

- `id`
- `species_id`

### Result

- `sigma_angstrom`
- `epsilon_over_k_k`
- `dipole_debye`
- `polarizability_angstrom3`
- `rotational_relaxation`

### Provenance

- `scientific_origin`
- `literature_id`
- `software_id`
- `workflow_tool_id`
- `created_by`
- `created_at`

### Curation

- `note`

## 4. species_entry_contributor

### Identity

- `id`
- `species_entry_id`
- `user_id`

### Result

- None

### Provenance

- `created_at`

### Curation

- `role`

## 5. geometry

### Identity

- `id`
- `natoms`
- `geom_hash`
- `xyz_text`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 6. geometry_atom

### Identity

- `geometry_id`
- `atom_index`
- `element`
- `x`
- `y`
- `z`

### Result

- None

### Provenance

- Inherited through `geometry_id`

### Curation

- None

## 7. chem_reaction

### Identity

- `id`
- `stoichiometry_hash`
- `reversible`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 8. reaction_participant

### Identity

- `reaction_id`
- `species_id`
- `role`
- `stoichiometry`

### Result

- None

### Provenance

- Inherited through `reaction_id`

### Curation

- None

## 9. reaction_entry

### Identity

- `id`
- `reaction_id`

### Result

- None

### Provenance

- `created_by`
- `created_at`

### Curation

- `preferred_ts_entry_id`

Note:

- this is the only preferred-pointer field in the initial schema that is not deferred

## 10. transition_state

### Identity

- `id`
- `reaction_entry_id`
- `label`

### Result

- None

### Provenance

- `created_by`
- `created_at`

### Curation

- `note`

## 11. transition_state_entry

### Identity

- `id`
- `transition_state_id`
- `charge`
- `multiplicity`
- `mol`
- `unmapped_smiles`

### Result

- None

### Provenance

- `created_by`
- `created_at`

### Curation

- `preferred_calculation_id`
- `status`

Note:

- `status` defaults to `optimized`

## 12. software

### Identity

- `id`
- `name`
- `version`
- `build`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 13. level_of_theory

### Identity

- `id`
- `method`
- `basis`
- `aux_basis`
- `dispersion`
- `solvent`
- `solvent_model`
- `keywords`
- `lot_hash`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 14. calculation

### Identity

- `id`
- `type`
- `species_entry_id`
- `transition_state_entry_id`

### Result

- None

### Provenance

- `software_id`
- `workflow_tool_id`
- `lot_id`
- `literature_id`
- `created_by`
- `created_at`

### Curation

- `quality`

Note:

- `quality` defaults to `raw`
- the enum type name is `calculation_quality`
- the XOR ownership check is named `ck_calculation_exactly_one_owner`

## 15. calculation_output_geometry

### Identity

- `calculation_id`
- `geometry_id`
- `output_order`

### Result

- None

### Provenance

- Inherited through `calculation_id`

### Curation

- `role`

Note:

- `role` uses the `calc_geom_role` enum with values `initial`, `final`, `intermediate`, `scan_point`, `irc_forward`, `irc_reverse`, `neb_image`

## 16. calculation_dependency

### Identity

- `parent_calculation_id`
- `child_calculation_id`

### Result

- None

### Provenance

- Inherited through the linked calculations

### Curation

- `dependency_role`

Note:

- `dependency_role` uses the `calc_dependency_role` enum with values `optimized_from`, `freq_on`, `single_point_on`, `arkane_source`, `irc_start`, `irc_followup`, `scan_parent`, `neb_parent`

## 17. calc_sp_result

### Identity

- `calculation_id`

### Result

- `electronic_energy_hartree`

### Provenance

- Inherited through `calculation_id`

### Curation

- None

## 18. calc_opt_result

### Identity

- `calculation_id`

### Result

- `converged`
- `n_steps`
- `final_energy_hartree`

### Provenance

- Inherited through `calculation_id`

### Curation

- None

## 19. calc_freq_results

### Identity

- `calculation_id`

### Result

- `n_imag`
- `img_freq_cm1`
- `zpe_hartree`

### Provenance

- Inherited through `calculation_id`

### Curation

- None

## 20. calculation_artifact

### Identity

- `id`
- `calculation_id`
- `kind`
- `uri`

### Result

- `sha256`
- `bytes`

### Provenance

- `created_at`

### Curation

- None

## 21. thermo

### Identity

- `id`
- `species_entry_id`

### Result

- `h298_kj_mol`
- `s298_j_mol_k`

### Provenance

- `scientific_origin`
- `literature_id`
- `workflow_tool_id`
- `software_id`
- `created_by`
- `created_at`

### Curation

- `note`

## 22. thermo_point

### Identity

- `thermo_id`
- `temperature_k`

### Result

- `cp_j_mol_k`
- `h_kj_mol`
- `s_j_mol_k`
- `g_kj_mol`

### Provenance

- Inherited through `thermo_id`

### Curation

- None

## 23. thermo_source_calculation

### Identity

- `thermo_id`
- `calculation_id`

### Result

- None

### Provenance

- Inherited through `thermo_id` and `calculation_id`

### Curation

- `role`

## 24. kinetics

### Identity

- `id`
- `reaction_entry_id`
- `model_kind`

### Result

- `a`
- `a_units`
- `n`
- `ea_kj_mol`
- `tmin_k`
- `tmax_k`
- `degeneracy`
- `tunneling_model`

### Provenance

- `scientific_origin`
- `literature_id`
- `workflow_tool_id`
- `software_id`
- `created_by`
- `created_at`

### Curation

- `note`

Note:

- `model_kind` is identity/classification for the stored law form and defaults to `modified_arrhenius`

## 25. kinetics_source_calculation

### Identity

- `kinetics_id`
- `calculation_id`

### Result

- None

### Provenance

- Inherited through `kinetics_id` and `calculation_id`

### Curation

- `role`

## 26. network

### Identity

- `id`
- `name`
- `description`

### Result

- None

### Provenance

- `literature_id`
- `software_id`
- `workflow_tool_id`
- `created_by`
- `created_at`

### Curation

- None

## 27. network_reaction

### Identity

- `network_id`
- `reaction_entry_id`

### Result

- None

### Provenance

- Inherited through `network_id`

### Curation

- None

## 28. network_species

### Identity

- `network_id`
- `species_id`

### Result

- None

### Provenance

- Inherited through `network_id`

### Curation

- `role`

Note:

- `role` is optional in the migration; unlabeled membership rows are allowed

## 29. literature

### Identity

- `id`
- `kind`
- `title`
- `journal`
- `year`
- `volume`
- `issue`
- `pages`
- `article_number`
- `doi`
- `isbn`
- `url`
- `publisher`
- `institution`

### Result

- None

### Provenance

- `created_by`
- `created_at`

### Curation

- None

## 30. author

### Identity

- `id`
- `given_name`
- `family_name`
- `full_name`
- `orcid`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 31. literature_author

### Identity

- `literature_id`
- `author_id`

### Result

- None

### Provenance

- Inherited through `literature_id` and `author_id`

### Curation

- `author_order`

Note:

- `author_order` must be greater than zero

## 32. workflow_tool

### Identity

- `id`
- `name`
- `version`
- `description`

### Result

- None

### Provenance

- `created_at`

### Curation

- None

## 33. app_user

### Identity

- `id`
- `username`
- `email`
- `full_name`
- `affiliation`
- `orcid`

### Result

- None

### Provenance

- `created_at`

### Curation

- `role`

Note:

- `role` defaults to `user`

## High-level observations

- Identity is concentrated in `species`, `chem_reaction`, `transition_state`, `geometry`, and the bibliographic/reference tables.
- Result values are intentionally pushed into typed result tables such as `calc_sp_result`, `calc_opt_result`, `calc_freq_results`, `thermo`, `thermo_point`, and `kinetics`.
- Provenance is carried mainly through `created_by`, `created_at`, `scientific_origin`, `literature_id`, `software_id`, `workflow_tool_id`, and link tables back to `calculation`.
- Curation currently appears as preferred pointers and qualitative status fields: `preferred_calculation_id`, `preferred_ts_entry_id`, `status`, `quality`, and role-like labeling fields in link tables.
