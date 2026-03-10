# TCKDB Schema Specification

## 1. Design Philosophy

The current schema separates four concerns:

- Identity: what the chemical or bibliographic thing is
- Result: computed or reported values about that thing
- Provenance: who created it, what software or literature it came from, and which calculations support it
- Curation: preferred pointers, status values, and quality labels

The main design choices are:

- `species` is a stable identity object with canonical unmapped identifiers
- `species_entry` and `transition_state_entry` are entry-level realizations that preserve submitted structure data
- `calculation` is the provenance hub for computational work
- typed result tables such as `calc_sp_result`, `calc_opt_result`, `calc_freq_result`, and scan/frequency detail tables store direct job outputs
- higher-level data products such as `transport`, `thermo`, and `kinetics` reference literature, software, and workflow tools; only `thermo` and `kinetics` also carry explicit source-calculation link tables

## 2. Core Identity Tables

### 2.1 Species

Represents a stable species identity.

Fields:

- `id`
- `kind` enum: `molecule`, `pseudo`
- `smiles`
- `inchi_key`
- `charge`
- `multiplicity`
- `created_at`

Constraints and notes:

- `inchi_key` is unique
- `smiles` is intended to be a canonical unmapped identity string
- `charge` and `multiplicity` are part of the identity
- `created_at` is `NOT NULL DEFAULT now()`

### 2.2 Reaction

Stored as `chem_reaction`.

Fields:

- `id`
- `stoichiometry_hash`
- `reversible`
- `created_at`

Constraints and notes:

- `stoichiometry_hash` is unique
- participants are stored separately in `reaction_participant`
- `created_at` is `NOT NULL DEFAULT now()`

### 2.3 Transition State

Stored as `transition_state`.

Fields:

- `id`
- `reaction_entry_id`
- `label`
- `note`
- `created_by`
- `created_at`

Constraints and notes:

- a transition state is reaction-centered in this schema
- it is not treated as a species-like global identity
- `created_at` is `NOT NULL DEFAULT now()`

### 2.4 Geometry

Represents a concrete 3D structure.

Fields:

- `id`
- `natoms`
- `geom_hash`
- `xyz_text`
- `created_at`

Related table:

- `geometry_atom(geometry_id, atom_index, element, x, y, z)`

Constraints and notes:

- `geom_hash` has an explicit unique btree index
- geometries are linked to calculations through `calculation_output_geometry`
- geometry is shared infrastructure, not directly owned by one table

## 3. Entry Tables

### 3.1 Species Entry

Represents a stationary-point realization of a species.

Fields:

- `id`
- `species_id`
- `kind` enum: `conformer`, `minimum`, `vdw_complex`
- `mol`
- `preferred_calculation_id`
- `preferred_thermo_id`
- `preferred_statmech_id`
- `created_by`
- `created_at`

Notes:

- `mol` preserves the submitted stationary-point representation
- `preferred_calculation_id` is a curated pointer to the chosen default calculation for this entry
- `preferred_thermo_id` is a curated pointer to the chosen default thermo record for this entry
- `preferred_statmech_id` is a curated pointer to the chosen default statmech record for this entry
- the FK to `preferred_calculation_id` is `DEFERRABLE INITIALLY DEFERRED`
- `created_at` is `NOT NULL DEFAULT now()`

### 3.2 Reaction Entry

Represents an entry-level realization of a reaction.

Fields:

- `id`
- `reaction_id`
- `preferred_ts_entry_id`
- `created_by`
- `created_at`

Notes:

- `preferred_ts_entry_id` is a curated pointer to the chosen TS entry for this reaction entry
- unlike the preferred calculation pointers, this FK is not deferred in the migration
- `created_at` is `NOT NULL DEFAULT now()`

### 3.3 Transition State Entry

Represents an entry-level TS candidate or validated TS structure.

Fields:

- `id`
- `transition_state_id`
- `charge`
- `multiplicity`
- `mol`
- `unmapped_smiles`
- `preferred_calculation_id`
- `status` enum: `guess`, `optimized`, `validated`, `rejected`
- `created_by`
- `created_at`

Notes:

- `mol` preserves the mapped/original TS structure
- `unmapped_smiles` is a de-mapped canonical display/search string derived from the same structure
- `charge` and `multiplicity` are stored on the TS entry itself
- `preferred_calculation_id` is a curated pointer to the chosen default calculation for this TS entry
- `status` defaults to `optimized`
- the FK to `preferred_calculation_id` is `DEFERRABLE INITIALLY DEFERRED`
- `created_at` is `NOT NULL DEFAULT now()`

## 4. Provenance and Reference Tables

### 4.1 Software

Fields:

- `id`
- `name`
- `version`
- `build`
- `created_at`

Constraint:

- unique on `(name, version)`

### 4.2 Workflow Tool

Fields:

- `id`
- `name`
- `version`
- `description`
- `created_at`

Constraint:

- unique on `(name, version)`

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

### 4.4 Literature

Fields:

- `id`
- `kind` enum: `article`, `book`, `thesis`, `report`, `dataset`, `webpage`
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
- `created_by`
- `created_at`

Constraints:

- non-unique indexes also exist on `doi` and `isbn`
- partial unique index on `doi` where not null
- partial unique index on `isbn` where not null

### 4.5 Author and Literature Author

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

Constraints:

- `author.orcid` unique
- `literature_author(literature_id, author_order)` unique
- `literature_author(literature_id, author_id)` unique
- `literature_author.author_order` must be greater than zero

### 4.6 App User

Fields:

- `id`
- `username`
- `email`
- `full_name`
- `affiliation`
- `orcid`
- `role` enum: `user`, `curator`, `admin`
- `created_at`

Constraints:

- unique on `username`
- unique on `email`
- unique on `orcid`

Notes:

- `role` defaults to `user`

## 5. Calculation Layer

### 5.1 Calculation

Represents one computational job.

Fields:

- `id`
- `type` enum: `opt`, `freq`, `sp`, `irc`, `scan`, `neb`, `conf`
- `quality` enum: `raw`, `curated`, `rejected`
- `species_entry_id`
- `transition_state_entry_id`
- `software_id`
- `workflow_tool_id`
- `lot_id`
- `literature_id`
- `created_by`
- `created_at`

Integrity rule:

- exactly one of `species_entry_id` or `transition_state_entry_id` must be non-null

Notes:

- this is the main computational provenance hub
- the owning entry is either a species entry or a TS entry, never both
- `quality` defaults to `raw`
- the enum type name is `calculation_quality`
- the XOR ownership check is named `ck_calculation_exactly_one_owner`
- `created_at` is `NOT NULL DEFAULT now()`

### 5.2 Calculation Output Geometry

Fields:

- `calculation_id`
- `geometry_id`
- `output_order`
- `role` enum: `initial`, `final`, `intermediate`, `scan_point`, `irc_forward`, `irc_reverse`, `neb_image`

Constraints:

- primary key on `(calculation_id, output_order)`
- unique on `(calculation_id, geometry_id)`
- the unique constraint is named `uq_calculation_output_geometry_calculation_id`

Notes:

- supports multiple geometries per calculation
- intended for final structures, scan points, IRC outputs, NEB images, and similar cases
- the enum type name is `calc_geom_role`

### 5.3 Calculation Dependency

Fields:

- `parent_calculation_id`
- `child_calculation_id`
- `dependency_role` enum: `optimized_from`, `freq_on`, `single_point_on`, `arkane_source`, `irc_start`, `irc_followup`, `scan_parent`, `neb_parent`

Constraints:

- primary key on `(parent_calculation_id, child_calculation_id)`
- self-loop check: parent and child cannot be the same

Notes:

- this is a lightweight provenance graph between calculations
- the enum type name is `calc_dependency_role`

### 5.4 Direct Calculation Result Tables

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
- `img_freq_cm1`
- `zpe_hartree`

`calc_freq_mode`:

- `calculation_id`
- `mode_index`
- `frequency_cm1`
- `reduced_mass_amu`
- `force_constant_mdyn_a`
- `ir_intensity_km_mol`
- `is_scaled`
- `is_projected`

`calc_hessian`:

- `calculation_id`
- `n_atoms`
- `matrix_dim`
- `units`
- `representation`
- `artifact_id`

`calc_scan_result`:

- `calculation_id`
- `scan_kind` enum: `torsion`, `bond`, `angle`, `multi_torsion`
- `dimension`
- `n_points`
- `converged`
- `note`

`calc_scan_coordinate`:

- `calculation_id`
- `coordinate_index`
- `coordinate_kind` enum: `torsion`, `bond`, `angle`
- `atom1_index`
- `atom2_index`
- `atom3_index`
- `atom4_index`
- `symmetry_number`
- `top_description`

`calc_scan_point`:

- `calculation_id`
- `point_index`
- `relative_energy_kj_mol`
- `geometry_id`
- `is_valid`

Notes:

- these tables store direct outputs of one calculation
- TS imaginary frequency is intentionally stored at the frequency-result level, not on `transition_state_entry`

### 5.5 Calculation Artifact

Fields:

- `id`
- `calculation_id`
- `kind` enum: `input`, `output_log`, `checkpoint`, `formatted_checkpoint`, `ancillary`
- `uri`
- `sha256`
- `bytes`
- `created_at`

Notes:

- stores file-level provenance for calculations
- indexes exist on `(calculation_id, kind)` and on `sha256`

## 6. Domain Result Tables

### 6.1 Transport

Fields:

- `id`
- `species_id`
- `scientific_origin` enum: `computed`, `experimental`, `estimated`
- `literature_id`
- `software_id`
- `workflow_tool_id`
- `sigma_angstrom`
- `epsilon_over_k_k`
- `dipole_debye`
- `polarizability_angstrom3`
- `rotational_relaxation`
- `note`
- `created_by`
- `created_at`

### 6.2 Thermo

Fields:

- `id`
- `species_entry_id`
- `statmech_id`
- `scientific_origin`
- `model_kind` enum: `nasa`, `shomate`, `tabulated`, `statmech`, `experimental`
- `literature_id`
- `workflow_tool_id`
- `software_id`
- `created_by`
- `created_at`
- `h298_kj_mol`
- `s298_j_mol_k`
- `note`

Related tables:

- `thermo_point(thermo_id, temperature_k, cp_j_mol_k, h_kj_mol, s_j_mol_k, g_kj_mol)`
- `thermo_nasa(thermo_id, t_low_k, t_mid_k, t_high_k, low_a1..low_a7, high_a1..high_a7)`
- `thermo_source_calculation(thermo_id, calculation_id, role)`

Notes:

- `model_kind` uses the `thermo_model_kind` enum
- `thermo_source_calculation.role` is one of `opt`, `freq`, `sp`, `composite`, `imported`

### 6.3 Statmech

Fields:

- `id`
- `species_entry_id`
- `scientific_origin`
- `literature_id`
- `workflow_tool_id`
- `software_id`
- `external_symmetry`
- `point_group`
- `is_linear`
- `rigid_rotor_kind` enum: `atom`, `linear`, `spherical_top`, `symmetric_top`, `asymmetric_top`
- `statmech_treatment` enum: `rrho`, `rrho_1d`, `rrho_nd`, `rrho_1d_nd`, `rrho_ad`, `rrao`
- `freq_scale_factor`
- `uses_projected_frequencies`
- `note`
- `created_by`
- `created_at`

Related tables:

- `statmech_source_calculation(statmech_id, calculation_id, role)`
- `statmech_torsion(id, statmech_id, torsion_index, symmetry_number, treatment_kind, dimension, top_description, invalidated_reason, note, source_scan_calculation_id)`
- `statmech_torsion_definition(torsion_id, coordinate_index, atom1_index, atom2_index, atom3_index, atom4_index)`

Notes:

- `statmech_source_calculation.role` is one of `opt`, `freq`, `sp`, `scan`, `composite`, `imported`
- `statmech_torsion.treatment_kind` is one of `hindered_rotor`, `free_rotor`, `rigid_top`, `hindered_rotor_dos`
- `statmech` has a deduplication unique constraint across species/provenance/treatment fields
- `external_symmetry` must be at least 1 when present
- `dimension` must be at least 1 on `statmech_torsion`

### 6.4 Kinetics

Fields:

- `id`
- `reaction_entry_id`
- `scientific_origin`
- `model_kind` enum: `arrhenius`, `modified_arrhenius`
- `literature_id`
- `workflow_tool_id`
- `software_id`
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

- `kinetics_source_calculation(kinetics_id, calculation_id, role)`

Notes:

- `model_kind` defaults to `modified_arrhenius`
- `kinetics_source_calculation.role` is one of `reactant_energy`, `product_energy`, `ts_energy`, `freq`, `irc`, `master_equation`, `fit_source`

## 7. Relationship and Membership Tables

### 7.1 Reaction Participant

Fields:

- `reaction_id`
- `species_id`
- `role` enum: `reactant`, `product`
- `stoichiometry`

Notes:

- stoichiometric multiplicity is carried in `stoichiometry`
- one row represents one species on one side of the reaction

### 7.2 Species Entry Contributor

Fields:

- `id`
- `species_entry_id`
- `user_id`
- `role` enum: `submitted`, `curated`, `computed`, `linked`
- `created_at`

Constraint:

- unique on `(species_entry_id, user_id, role)`

### 7.3 Network

Fields:

- `id`
- `name`
- `description`
- `literature_id`
- `software_id`
- `workflow_tool_id`
- `created_by`
- `created_at`

Related tables:

- `network_reaction(network_id, reaction_entry_id)`
- `network_species(network_id, species_id, role)`

Notes:

- `network_species.role` may be null in the migration
- when present, `network_species.role` is one of `well`, `reactant`, `product`, `bath_gas`

## 8. Important Integrity Rules

- `calculation` has an XOR check on `species_entry_id` vs `transition_state_entry_id`
- `calculation_output_geometry` prevents duplicate `(calculation_id, geometry_id)` pairs
- `calculation_dependency` prevents self-edges
- `species_entry.preferred_calculation_id` and `transition_state_entry.preferred_calculation_id` are deferred foreign keys to support transactional creation order
- `reaction_entry.preferred_ts_entry_id` is a normal immediate FK, not deferred
- semantic ownership of preferred calculations is currently enforced in application logic, not by the database

## 9. Current Semantic Model

- `species.smiles` and `species.inchi_key` are stable identity descriptors
- `species_entry.mol` preserves submitted stationary-point structure data
- `transition_state_entry.mol` preserves the mapped TS representation
- `transition_state_entry.unmapped_smiles` is for cleaner display/search, not species-style global identity
- `preferred_*` fields are curation pointers, not provenance by themselves
- direct computational facts live in calculation result tables; curated scientific products live in domain result tables
