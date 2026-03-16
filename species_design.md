# Species Design Logic

This note explains the conceptual model behind the `species`, `species_entry`,
and `conformer` tables, and why conformer identity is stable, while conformer assignment and selection logic are recorded in a separate, versioned provenance layer.

## 1. Chemical Identity Hierarchy

The database separates molecular identity into three levels because they
represent different physical concepts.

### Level 1: `species` (2D chemical identity)

`species` represents the bond-connectivity graph.

It answers:

- What atoms exist?
- How are they bonded?
- What are the charge and multiplicity?

Examples:

- HOCO
- ethanol
- benzene

This level intentionally ignores:

- stereochemistry
- conformers
- 3D geometry

Reason:

The chemical formula and connectivity define the molecule class.

### Level 2: `species_entry` (resolved chemical form)

`species_entry` represents a specific resolved chemical form of a `species`.

This includes:

- stereochemistry
- cis/trans isomerism
- electronic state
- isotopologues

Examples for HOCO:

- cis-HOCO (doublet)
- trans-HOCO (doublet)
- HOCO excited state

This level corresponds to what a chemist would typically consider a distinct
molecular species for thermochemistry or kinetics.

Important point:

Thermochemistry and statistical mechanics attach here because they describe the
molecular form, not an individual conformer.

### Level 3: `conformer` (3D geometry realization)

`conformer` represents a deduplicated conformational minimum or basin of a `species_entry`. It is not a single uploaded geometry. Multiple calculations and geometries may map to the same conformer if they correspond to the same underlying minimum.

Examples:

- gauche ethanol conformer
- anti ethanol conformer
- one optimized HOCO geometry

Each conformer corresponds to a local minimum or candidate structure.

Conformers are where calculations and geometries attach.

### Why this hierarchy is chemically correct

Chemists already think in these layers:

```text
connectivity
    ↓
stereochemical identity
    ↓
3D conformations
```

Or, in table terms:

```text
Species
   ↓
SpeciesEntry
   ↓
Conformer
```

This mirrors the physical hierarchy of molecular identity.

## 2. Why Conformer Assignment Cannot Be Fixed

Determining whether two geometries represent the same conformer is not
absolute.

It depends on:

- torsion thresholds
- symmetry handling
- which torsions are treated as conformationally meaningful
- secondary geometric descriptors used in borderline cases

For example, two HOCO geometries might be classified differently depending on:

- whether classification is based on dihedral angles
- whether mirror images are merged
- whether a borderline case is split by RMSD or accepted into an existing bin

Therefore, the logic used to assign uploaded geometries to conformers, and the logic used to select representative conformers for downstream workflows, should be versionable and replaceable.

Important rule:

Level of theory is provenance, not conformer identity.

The binning strategy should use torsional state as the main discriminator, while
keeping thresholds and special-case logic versioned in
`conformer_assignment_scheme`.

## 3. Practical Binning Strategy

The intended workflow is:

### Step 1: resolve `species` and `species_entry`

Before conformer assignment, the uploaded structure must already be resolved to
the correct connectivity and resolved molecular form.

### Step 2: compute a torsion fingerprint

From the candidate geometry, compute a torsion fingerprint using only
conformationally meaningful torsions.

This is the primary conformer discriminator.

### Step 3: compare against existing conformers of that `species_entry`

Compare the candidate fingerprint to existing conformers using:

- periodic-aware torsion differences
- symmetry-aware handling where possible
- versioned thresholds such as 15 degrees on key torsions

### Step 4: use secondary checks for borderline cases

If torsional comparison is ambiguous, apply secondary checks such as:

- aligned RMSD
- energy proximity
- ring-pucker descriptors for cyclic systems

### Step 5: assign or create

If the geometry matches an existing conformer basin, assign it to that
conformer. Otherwise, create a new conformer.

This is a defensible workflow because it keeps the main decision on chemically
meaningful torsional state, while leaving room for secondary geometric evidence
when torsions are not enough.

## 4. Why Torsions Are Primary, But Not Always Sufficient

Torsions are usually the main determinant for conformer assignment, but not
always sufficient by themselves.

Cases where torsions alone may fail include:

- pyramidal inversion
- ring puckering
- near-linear systems
- weakly bound complexes
- chirality emerging from 3D arrangement
- proton-transfer-like shallow rearrangements

The honest formulation is:

torsions are the primary determinant for conformer assignment in most cases,
with optional secondary geometric descriptors where needed.

## 5. Separation of Conformer Identity From Assignment Rules

The design stores stable conformers separately from the versioned logic used to
interpret or select them.

Stable layer (scientific objects):

```text
species
   ↓
species_entry
   ↓
conformer
```

These objects should not change meaning over time.

Interpretation and provenance layer:

```text
conformer_assignment_scheme
        ↓
conformer_selection
```

This layer answers:

- what algorithm or rules were used
- which scheme version a selection came from
- how representative or default conformers were chosen

For example:

Scheme A may define how `lowest_energy` or `display_default` are selected.

Scheme B may use a different energy cutoff or symmetry convention.

Both schemes can coexist without changing the underlying conformers.

## 6. Selection Layer

Selections identify useful representatives.

Examples:

- lowest-energy conformer
- display default
- representative geometry

These are stored in `conformer_selection` and can be scoped to a specific
`conformer_assignment_scheme`.

This avoids putting subjective choices such as "preferred conformer" directly
into identity tables.

## 7. Example Workflow

Two users upload HOCO geometries.

### Step 1: species resolution

Both map to:

```text
species = HOCO
```

### Step 2: species-entry resolution

Geometry analysis determines:

```text
species_entry = cis-HOCO
```

### Step 3: torsion-first conformer comparison

The new geometry is compared to existing conformers of `species_entry = cis-HOCO`
using a torsion fingerprint and periodic/symmetry-aware thresholds.

If it clearly matches an existing conformer basin:

```text
attach calculations to conformer_3
```

Otherwise:

```text
create new conformer_7
```

If the result is borderline, secondary checks such as aligned RMSD, energy
proximity, or ring-pucker descriptors can be used before deciding.

### Step 4: assignment-aware selection

Under canonical scheme `v1`:

```text
selection: lowest_energy
conformer: conformer_3
```

Under a future scheme:

```text
selection: lowest_energy
conformer: conformer_7
```

The conformer objects remain unchanged.

### Step 5: calculation attachment

If a job is tied to a specific conformer:

```text
calculation.conformer_id = conformer_3
```

If a job is only resolved to the entry level:

```text
calculation.species_entry_id = species_entry(cis-HOCO)
```

If the job belongs to the TS side instead:

```text
calculation.transition_state_entry_id = ts_entry_12
```

## 8. Why This Design Is Robust

This design provides:

- Scientific correctness: identity is separated from interpretation.
- Reproducibility: assignment and selection schemes are versioned.
- Flexibility: torsion thresholds, symmetry rules, and secondary checks can
  evolve without restructuring the database.
- Provenance: assignment schemes capture method, parameters, creator, and
  version.
- Method clarity: torsional state is the main conformer discriminator, while
  level of theory remains provenance rather than identity.

## 9. One-Sentence Explanation

The database separates molecular identity from conformer interpretation:
`species` defines connectivity, `species_entry` defines stereochemical or
electronic identity, and `conformer` represents a specific 3D structure, while
versioned assignment schemes record torsion-first heuristics and selection logic
without changing the core molecular records.

## 10. Visual Diagram

```text
Species
   │
   └── SpeciesEntry
         │
         └── Conformer
               │
               ├── Calculation
               └── Geometry

ConformerAssignmentScheme
        │
        └── ConformerSelection

Calculation
   ├── species_entry_id
   ├── conformer_id
   └── transition_state_entry_id
```

## 11. The Real Conceptual Shift

Old idea:

Conformers are defined by level of theory, clustering behavior, or whatever
selection logic happens to be active.

New idea:

Conformers exist independently. Assignment schemes only encode the heuristics
used to bin geometries and make selections.

That separation is what makes the database stable.
