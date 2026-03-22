# DR-0003: Energy Correction Two-Layer Architecture

**Date:** 2026-03-21
**Status:** Accepted
**Authors:** Calvin, Claude

## Context

Computational thermochemistry workflows apply multiple types of energy corrections to raw electronic structure results before reporting derived quantities (enthalpies of formation, reaction barriers, etc.). These corrections include:

- **Atomic reference data**: atom enthalpies of formation (atom_hf), atom thermal corrections (atom_thermal), spin-orbit coupling constants (SOC), and total atomic energies — all keyed by element and level of theory.
- **Bond additivity corrections (BAC)**: Petersson-type BAC parameters keyed by bond type (C-H, C=C, O=S); Melius-type BAC with separate atom_corr, bond_corr_length, bond_corr_neighbor, and mol_corr components.
- **Frequency scale factors**: multiplicative factors keyed by level of theory and scale kind (ZPE, fundamental, enthalpy, entropy).

These parameters are reusable across many calculations — they come from published papers and fitted datasets. However, the *application* of these parameters to a specific species or reaction is study-specific: two researchers may upload the same conformer geometry but apply different BAC schemes, different atomic energy references, or different frequency scale factors depending on their workflow (e.g., Arkane vs. a custom pipeline).

TCKDB needed a schema that cleanly stores both the reusable parameter libraries and the per-entry applied correction records, without conflating the two.

## Considered Alternatives

### Alternative A: Single flat correction table

- **Description:** One table with columns for every correction type (bac_total, zpe_correction, atom_energy_correction, etc.), attached directly to the conformer or calculation record.
- **Pros:** Simple queries; one row per corrected entity.
- **Cons / why rejected:** Mixes parameter definitions with applied results. Cannot represent reusable parameter sets across calculations. Adding a new correction type requires schema migration. Cannot record per-component breakdown (e.g., which bonds contributed to BAC). Forces conformer-level ownership, which breaks when two studies share a deduped conformer but use different correction schemes.

### Alternative B: Generic key-value correction store

- **Description:** A single `correction` table with `(entity_id, correction_type, key, value)` rows, storing both parameters and applied results as unstructured key-value pairs.
- **Pros:** Maximally flexible; no schema changes for new correction types.
- **Cons / why rejected:** No type safety or structural enforcement. Cannot distinguish parameter definitions from applied results. Cannot enforce that a Petersson BAC scheme contains bond-keyed parameters while a Melius scheme contains component-keyed parameters. Provenance linkage (which literature, which level of theory) would require additional columns or a separate table anyway, converging toward the chosen design.

### Alternative C: Correction owned by conformer group

- **Description:** Attach `applied_energy_correction` rows to `conformer_group.id` (the deduped structural grouping) rather than to the species entry.
- **Pros:** Direct structural link; one conformer → its corrections.
- **Cons / why rejected:** Conformer groups are shared across uploads by design (deduplication). Two users uploading the same conformer geometry would be forced to share correction records, which is scientifically incorrect — they may use different BAC schemes, different literature sources, different frequency scale factors. Correction provenance must remain study-scoped, not structure-scoped. The correct pattern is: shared conformer identity, separate correction provenance.

## Decision

Adopt a **two-layer architecture** separating reusable correction parameter definitions from per-entry applied correction results:

**Reference layer** (parameter libraries):
- `energy_correction_scheme` — top-level scheme with kind, name, level of theory, literature source, version
- `energy_correction_scheme_atom_param` — element → value mappings (composite PK: scheme + element)
- `energy_correction_scheme_bond_param` — bond-type → value mappings (composite PK: scheme + bond_key)
- `energy_correction_scheme_component_param` — Melius BAC multi-component parameters (composite PK: scheme + component_kind + key)
- `frequency_scale_factor` — separate first-class entity (level of theory + scale kind → value)

**Application layer** (per-entry results):
- `applied_energy_correction` — links a scheme + application role to a target entry, with value, unit, optional temperature, and source provenance (conformer observation, calculation)
- `applied_energy_correction_component` — optional per-component breakdown for auditability

Two key fields on `applied_energy_correction` serve distinct purposes:
- `scheme_id` (NOT NULL) — answers "what reusable parameter set was used?"
- `application_role` (NOT NULL, enum) — answers "what semantic quantity does this row represent?" (e.g., zpe, thermal_correction_enthalpy, bac_total, aec_total)

This distinction is necessary because one scheme kind can produce multiple applied quantities (e.g., a frequency-derived scheme yields both ZPE and thermal corrections).

## Scientific Justification

The separation of parameter libraries from applied results reflects standard practice in computational thermochemistry workflows:

1. **Parameter reusability.** Atomic reference energies, BAC parameters, and frequency scale factors are published constants (e.g., Petersson et al., Melius & Binkley, Alecu et al. 2010 for scale factors). They are versioned, literature-sourced, and shared across hundreds of calculations. Storing them as first-class entities enables provenance tracking and prevents inconsistent parameter duplication.

2. **Application heterogeneity.** The same molecule computed at the same level of theory may be corrected differently depending on the workflow. ARC/Arkane may apply Petersson BAC; a different group may use Melius BAC or no BAC at all. The same ZPE may be scaled by different factors from different literature sources. These are distinct scientific assertions and must remain separate records.

3. **Conformer deduplication compatibility.** TCKDB deduplicates conformer geometries into shared groups. If corrections were attached to the shared group, provenance would be lost or conflated. By attaching corrections to the species entry (the provenance-bearing record), deduplication of structure and separation of correction provenance are fully compatible.

4. **Auditability.** The per-component breakdown (Option 2 from the design discussion) enables answering questions like: "Which BAC scheme was used? Which bonds contributed? Was SOC included in the atomic energies? Why does this corrected enthalpy differ from another workflow's result?" This is essential for a reference database where reproducibility and traceability are primary goals.

5. **Application role vs. scheme kind.** The `application_role` enum captures the semantic meaning of the applied result (zpe, thermal_correction_enthalpy, bac_total, etc.) independently from the scheme's category. This mirrors how thermochemistry workflows produce multiple derived quantities from a single set of parameters — e.g., a frequency calculation yields ZPE, thermal energy, thermal enthalpy, and thermal Gibbs corrections, each potentially scaled differently.

## Implementation Notes

- **Enums** in `app/db/models/common.py`: `EnergyCorrectionSchemeKind`, `MeliusBacComponentKind`, `FrequencyScaleKind`, `AppliedCorrectionComponentKind`, `EnergyCorrectionApplicationRole`
- **ORM models** in `app/db/models/energy_correction.py`: 7 classes covering both layers
- **Pydantic schemas** in `app/schemas/entities/energy_correction.py`: Base/Create/Read/Update for each entity
- **Target FKs** are entry-level: `target_species_entry_id` → `species_entry.id`, `target_reaction_entry_id` → `reaction_entry.id`
- **Source provenance**: `source_conformer_observation_id` → `conformer_observation.id` (the uploaded instance, not the deduped group), `source_calculation_id` → `calculation.id`
- **Constraint**: at most one target FK populated (simple CheckConstraint, no discriminator enum needed with only two target types)
- **Dedup index**: unique on (target entries, source conformer, scheme, application_role, temperature, source calculation) with NULLS NOT DISTINCT

## Limitations & Future Work

- **No upload workflow schema yet.** The entity schemas use integer FK IDs for resolved data. An upload/workflow schema (in `app/schemas/workflows/`) will be needed that accepts string key cross-references (e.g., `source_conformer_key: "conf_obs_1"`) and resolves them to IDs during persistence.
- **No correction service.** Resolution logic (scheme lookup/creation, applied correction persistence) has not been implemented yet. This will follow the established pattern in `app/services/`.
- **`application_role` enum may grow.** The initial set covers common thermochemistry quantities, but the `custom` value provides an escape hatch. New roles can be added via Alembic enum migration as workflows mature.
- **Frequency scale factors are separate.** `frequency_scale_factor` is not a child of `energy_correction_scheme` because frequency scaling is conceptually distinct from BAC/atom energy corrections. If this distinction proves unnecessary, the tables could be unified in a future revision.
- **No transition state or network targets yet.** `applied_energy_correction` currently targets species entries and reaction entries. Transition state and network targets can be added via migration if needed.

## References

- Petersson, G. A. et al. (1991). "A complete basis set model chemistry." *J. Chem. Phys.* 94, 6081. (Petersson BAC methodology)
- Melius, C. F.; Binkley, J. S. (1986). "Thermochemistry of the decomposition of nitramines." *Symp. (Int.) Combust.* 21, 1953. (Melius BAC methodology)
- Alecu, I. M. et al. (2010). "Computational Thermochemistry: Scale Factor Databases and Scale Factors for Vibrational Frequencies." *J. Chem. Theory Comput.* 6, 2872. (Frequency scale factors)
- DR-0001: Pressure-Dependent Kinetics Architecture (related architectural decision for network/pdep tables)
