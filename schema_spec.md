# TCKDB Schema Specification

## 1. Design Philosophy

The schema separates four concerns:

- Identity: what the chemical, bibliographic, or provenance object is
- Result: direct computed or reported values
- Provenance: software, workflow, literature, and source-calculation context
- Curation: human review, selection, and preferred display layers

The main structural choices are:

- `species` stores graph identity only
- `species_entry` refines stereo, electronic-state, and isotopologue meaning
- `conformer_group` stores basin identity, while `conformer_observation` stores per-calculation assignment/provenance
- `transition_state` is reaction-centered rather than species-centered
- `calculation` is the hub for computational provenance
- direct job outputs live in `calc_sp_result`, `calc_opt_result`, and `calc_freq_result`
- curated scientific products such as `statmech`, `transport`, `thermo`, and `kinetics` reference literature plus software/workflow provenance
- software and workflow provenance are both split into stable identity tables plus exact release/version tables

## 2. Core Identity Tables

### 2.1 Species

Fields:

- `id`
- `kind`
- `smiles`
- `inchi_key`
- `charge`
- `multiplicity`
- `created_at`

Notes:

- `inchi_key` is unique
- `smiles` is the canonical unmapped identity string
- `charge` and `multiplicity` are part of species identity
- `multiplicity` must be at least 1

### 2.2 Species Entry

Fields:

- `id`
- `species_id`
- `kind`
- `mol`
- `unmapped_smiles`
- `stereo_kind`
- `stereo_label`
- `electronic_state_kind`
- `electronic_state_label`
- `term_symbol_raw`
- `term_symbol`
- `isotopologue_label`
- `created_by`
- `created_at`

Notes:

- `species_entry` carries resolved stereo, electronic-state, and isotopic meaning
- `term_symbol_raw` is provenance, not identity
- `species_entry_identity_uq` is a unique identity constraint
- nullable identity components are deduped with PostgreSQL `NULLS NOT DISTINCT`

### 2.3 Chem Reaction and Reaction Entry

`chem_reaction` fields:

- `id`
- `stoichiometry_hash`
- `reversible`
- `created_at`

`reaction_entry` fields:

- `id`
- `reaction_id`
- `created_by`
- `created_at`

Notes:

- `stoichiometry_hash` is unique
- `reaction_entry` no longer carries preferred TS or preferred kinetics pointers
- `reaction_participant` is a compressed stoichiometric summary, not an ordered participant-slot table
- `reaction_participant.stoichiometry` must be at least 1

### 2.4 Transition State and Transition State Entry

`transition_state` fields:

- `id`
- `reaction_entry_id`
- `label`
- `note`
- `created_by`
- `created_at`

`transition_state_entry` fields:

- `id`
- `transition_state_id`
- `charge`
- `multiplicity`
- `mol`
- `unmapped_smiles`
- `status`
- `created_by`
- `created_at`

Notes:

- `transition_state` is the reaction-channel-level TS concept
- `transition_state_entry` is the candidate saddle-point geometry / TS conformer-like object
- calculations refine a `transition_state_entry`, and `transition_state_selection` marks the preferred one
- transition-state identity is reaction-centered
- `transition_state_entry` no longer carries a preferred calculation pointer
- `transition_state_entry.multiplicity` must be at least 1

### 2.5 Geometry

`geometry` fields:

- `id`
- `natoms`
- `geom_hash`
- `xyz_text`
- `created_at`

`geometry_atom` fields:

- `geometry_id`
- `atom_index`
- `element`
- `x`
- `y`
- `z`

Notes:

- `geom_hash` is unique
- geometry is shared infrastructure, linked to calculations through input/output link tables
- `natoms` must be at least 1

## 3. Conformer Layer

### 3.1 Conformer Group

Fields:

- `id`
- `species_entry_id`
- `label`
- `note`
- `created_by`
- `created_at`

Notes:

- this is the deduplicated conformational basin identity
- non-null labels are unique within a `species_entry`

### 3.2 Conformer Observation

Fields:

- `id`
- `conformer_group_id`
- `calculation_id`
- `assignment_scheme_id`
- `scientific_origin`
- `note`
- `created_by`
- `created_at`

Notes:

- this is the per-calculation assignment/provenance row
- `calculation_id` is unique here, so one calculation maps to at most one conformer observation

### 3.3 Conformer Assignment Scheme and Selection

`conformer_assignment_scheme` fields:

- `id`
- `name`
- `version`
- `scope`
- `description`
- `parameters_json`
- `code_commit`
- `is_default`
- `created_by`
- `created_at`

`conformer_selection` fields:

- `id`
- `conformer_group_id`
- `assignment_scheme_id`
- `selection_kind`
- `note`
- `created_by`
- `created_at`

Notes:

- assignment schemes describe how grouping or selection logic was produced
- selections are curation/annotation, not identity
- `conformer_selection_kind_uq` treats `NULL` `assignment_scheme_id` values as identical for dedupe

### 3.4 Species Entry Review

Fields:

- `id`
- `species_entry_id`
- `user_id`
- `role`
- `note`
- `created_at`

Constraint:

- unique on `(species_entry_id, user_id, role)`

## 4. Provenance and Reference Tables

### 4.1 Software and Software Release

`software` fields:

- `id`
- `name`
- `website`
- `description`
- `created_at`

`software_release` fields:

- `id`
- `software_id`
- `version`
- `revision`
- `build`
- `release_date`
- `notes`
- `created_at`

Notes:

- `software` is the stable identity
- `software_release` is the exact executable-level provenance
- release dedupe uses PostgreSQL `NULLS NOT DISTINCT` across `(software_id, version, revision, build)`

### 4.2 Workflow Tool and Workflow Tool Release

`workflow_tool` fields:

- `id`
- `name`
- `description`
- `created_at`

`workflow_tool_release` fields:

- `id`
- `workflow_tool_id`
- `version`
- `git_commit`
- `release_date`
- `notes`
- `created_at`

Notes:

- `workflow_tool` is the stable tool identity, such as ARC or RMG
- `workflow_tool_release` captures the exact code state used
- dependent scientific/provenance records point to `workflow_tool_release_id`
- release dedupe uses PostgreSQL `NULLS NOT DISTINCT` across `(workflow_tool_id, version, git_commit)`

### 4.3 Level of Theory

Fields:

- `id`
- `method`
- `basis`
- `aux_basis`
- `dispersion`
- `solvent`
- `solvent_model`
- `keywords`
- `lot_hash`
- `created_at`

Constraint:

- `lot_hash` is unique

### 4.4 Literature, Author, and Literature Author

`literature` fields:

- `id`
- `kind`
- `title`
- `journal`
- `year`
- `volume`
- `issue`
- `pages`
- `doi`
- `isbn`
- `url`
- `publisher`
- `institution`
- `created_at`

`author` fields:

- `id`
- `given_name`
- `family_name`
- `full_name`
- `orcid`
- `created_at`

`literature_author` fields:

- `literature_id`
- `author_id`
- `author_order`

Notes:

- `author.orcid` is unique
- `literature` has non-unique indexes on `doi` and `isbn`
- `literature_author` uses a composite primary key on `(literature_id, author_id)`
- `literature_author(literature_id, author_order)` is also unique

### 4.5 App User

Fields:

- `id`
- `username`
- `email`
- `full_name`
- `affiliation`
- `orcid`
- `role`
- `created_at`

Notes:

- `username`, `email`, and `orcid` are unique
- `role` defaults to `user`

## 5. Calculation Layer

### 5.1 Calculation

Fields:

- `id`
- `type`
- `quality`
- `species_entry_id`
- `transition_state_entry_id`
- `software_release_id`
- `workflow_tool_release_id`
- `lot_id`
- `literature_id`
- `created_by`
- `created_at`

Integrity rule:

- a calculation is either species-entry-owned or transition-state-entry-owned

Notes:

- `quality` defaults to `raw`
- `software_release_id` points to `software_release.id`
- `workflow_tool_release_id` points to `workflow_tool_release.id`
- exactly one of `species_entry_id` or `transition_state_entry_id` must be non-null

### 5.2 Geometry Link Tables

`calculation_input_geometry` fields:

- `calculation_id`
- `geometry_id`
- `input_order`

`calculation_output_geometry` fields:

- `calculation_id`
- `geometry_id`
- `output_order`
- `role`

Notes:

- input geometry supports multiple ordered geometries per calculation
- input rows are unique on `(calculation_id, geometry_id)`
- output geometry supports multiple geometries per calculation
- output rows are unique on `(calculation_id, geometry_id)`
- `input_order` and `output_order` must both be at least 1

### 5.3 Calculation Dependency

Fields:

- `parent_calculation_id`
- `child_calculation_id`
- `dependency_role`

Notes:

- primary key is `(parent_calculation_id, child_calculation_id)`
- `dependency_role` is required
- self-loops are forbidden
- selected roles enforce at most one parent per child via filtered unique indexes:
  `optimized_from`, `freq_on`, `single_point_on`, `scan_parent`, `neb_parent`
- DBML cannot represent those filtered unique indexes exactly; the PostgreSQL predicates are the source of truth
- full acyclicity should be enforced in application logic if the dependency graph must stay a DAG

### 5.4 Direct Result Tables

`calc_sp_result`:

- `calculation_id`
- `electronic_energy_hartree`

`calc_opt_result`:

- `calculation_id`
- `converged`
- `n_steps`
- `final_energy_hartree`

`calc_freq_result`:

- `calculation_id`
- `n_imag`
- `imag_freq_cm1`
- `zpe_hartree`

`calculation_artifact`:

- `id`
- `calculation_id`
- `kind`
- `uri`
- `sha256`
- `bytes`
- `created_at`

## 6. Scientific Product Tables

### 6.1 Statmech

Fields:

- `id`
- `species_entry_id`
- `scientific_origin`
- `literature_id`
- `workflow_tool_release_id`
- `software_release_id`
- `external_symmetry`
- `point_group`
- `is_linear`
- `rigid_rotor_kind`
- `statmech_treatment`
- `freq_scale_factor`
- `uses_projected_frequencies`
- `note`
- `created_by`
- `created_at`

Related tables:

- `statmech_source_calculation`
- `statmech_torsion`
- `statmech_torsion_definition`

Notes:

- dedupe is across `(species_entry_id, scientific_origin, workflow_tool_release_id, software_release_id, statmech_treatment)`
- nullable provenance fields in that dedupe rule use PostgreSQL `NULLS NOT DISTINCT`

### 6.2 Transport

Fields:

- `id`
- `species_entry_id`
- `scientific_origin`
- `literature_id`
- `software_release_id`
- `workflow_tool_release_id`
- `sigma_angstrom`
- `epsilon_over_k_k`
- `dipole_debye`
- `polarizability_angstrom3`
- `rotational_relaxation`
- `note`
- `created_by`
- `created_at`

Notes:

- `sigma_angstrom` and `epsilon_over_k_k` must be positive when present
- `rotational_relaxation` must be non-negative when present

### 6.3 Thermo

Fields:

- `id`
- `species_entry_id`
- `scientific_origin`
- `literature_id`
- `workflow_tool_release_id`
- `software_release_id`
- `created_by`
- `created_at`
- `h298_kj_mol`
- `s298_j_mol_k`
- `note`

Related tables:

- `thermo_point`
- `thermo_nasa`
- `thermo_source_calculation`

Notes:

- `thermo` no longer carries `statmech_id` or `model_kind`
- dedupe is across `(species_entry_id, scientific_origin, workflow_tool_release_id, software_release_id)`
- nullable provenance fields in that dedupe rule use PostgreSQL `NULLS NOT DISTINCT`
- `thermo_point` stores tabulated `H`, `S`, and `G`
- `thermo_nasa` uses `t_low`, `t_mid`, `t_high`, `a1..a7`, and `b1..b7`
- `thermo_nasa` is the fitted representation that carries Cp behavior
- `thermo_nasa` enforces increasing positive temperature bounds when present
- `thermo_nasa` requires `t_low`, `t_mid`, and `t_high` to be present together or absent together

### 6.4 Kinetics

Fields:

- `id`
- `reaction_entry_id`
- `scientific_origin`
- `model_kind`
- `literature_id`
- `workflow_tool_release_id`
- `software_release_id`
- `created_by`
- `created_at`
- `a`
- `a_units`
- `n`
- `ea_kj_mol`
- `tmin_k`
- `tmax_k`
- `degeneracy`
- `tunneling_model`
- `note`

Related table:

- `kinetics_source_calculation`

Notes:

- `model_kind` is limited to `arrhenius` and `modified_arrhenius`
- `a_units` and `tunneling_model` are free-text fields

## 7. Membership and Selection Tables

### 7.1 Reaction Participant

Fields:

- `reaction_id`
- `species_id`
- `role`
- `stoichiometry`

### 7.2 Reaction Entry Structure Participant

Fields:

- `id`
- `reaction_entry_id`
- `species_entry_id`
- `role`
- `participant_index`
- `note`
- `created_by`
- `created_at`

Notes:

- this is the ordered, entry-level species-entry assignment layer for a reaction entry
- unique on `(reaction_entry_id, role, participant_index)`

### 7.3 Transition State Selection

Fields:

- `id`
- `transition_state_id`
- `transition_state_entry_id`
- `selection_kind`
- `note`
- `created_by`
- `created_at`

Notes:

- unique on `(transition_state_id, selection_kind)`
- the selected `transition_state_entry_id` must belong to the same `transition_state_id`
- application logic must ensure the selected entry belongs to the same transition state

### 7.4 Network

`network` fields:

- `id`
- `name`
- `description`
- `literature_id`
- `software_release_id`
- `workflow_tool_release_id`
- `created_by`
- `created_at`

Related tables:

- `network_reaction(network_id, reaction_entry_id)`
- `network_species(network_id, species_entry_id, role)`

Notes:

- `network_species.role` is required
- primary key on `network_species` is `(network_id, species_entry_id, role)`

## 8. Important Integrity Rules

- `calculation` ownership is exclusive between species-entry and TS-entry paths
- `calculation_input_geometry` supports multiple ordered input geometries per calculation
- `calculation_output_geometry` prevents duplicate `(calculation_id, geometry_id)` pairs
- `calculation_dependency` prevents self-edges
- `species_entry` has a hard uniqueness constraint on its resolved identity tuple
- `conformer_group` labels are unique within a `species_entry`
- `conformer_observation` makes calculation-to-conformer assignment explicit rather than storing it on `calculation`

## 9. Current Semantic Model

- `species` and `species_entry` separate graph identity from resolved molecular meaning
- `conformer_group` is stable basin identity
- `conformer_observation` is the per-calculation conformer assignment record
- `calculation` stores computational provenance, not curated preferred selections
- `transition_state_selection` and `conformer_selection` are curation layers
- `software_release` and `workflow_tool_release` capture exact executable/code provenance
- higher-level scientific products reference literature plus exact software/workflow provenance and optional supporting calculations
