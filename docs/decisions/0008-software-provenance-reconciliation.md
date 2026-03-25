# DR-0008: Software Provenance Reconciliation — Declared vs Observed

**Date:** 2026-03-25
**Status:** Accepted
**Authors:** Calvin (design rationale), Claude (implementation)

## Context

Every electronic structure calculation is performed by a specific software version (e.g., Gaussian 09 Revision D.01, ORCA 5.0.4). Accurate software provenance is critical for reproducibility and for interpreting software-specific keywords.

TCKDB already has a user-declared path: uploads include a `SoftwareReleaseRef` (name, version, revision, build) that resolves to a `software_release` row. However, users frequently get version details wrong:
- They remember "Gaussian 16" but not the revision.
- They type ORCA 5 when it was ORCA 4.2.
- Wrapper workflows may launch a different executable than expected.
- Cluster module systems may load unexpected versions.

Meanwhile, output log files contain authoritative version banners (e.g., `Gaussian 09: EM64L-G09RevD.01 24-Apr-2013` or `Program Version 5.0.4`). These are strong evidence of what actually ran.

## Considered Alternatives

### Alternative A: Trust user declaration only

- **Description:** Accept the user-provided software version without verification.
- **Pros:** Simple. No parser dependency.
- **Cons / why rejected:** Users get this wrong regularly. Silent provenance errors propagate into the database.

### Alternative B: Extract from output only, ignore user input

- **Description:** Parse the version banner from log files; do not accept user declarations.
- **Pros:** Most accurate for well-formed logs.
- **Cons / why rejected:** Not every artifact has a parseable banner (truncated, reformatted, or secondary data sources). Makes the database dependent on parser success for a critical field. Removes explicit provenance from the upload contract.

### Alternative C: Dual-source reconciliation (chosen)

- **Description:** User declares software version; parser extracts it from the log; a reconciliation service compares and decides.
- **Pros:** Strongest provenance model. Catches errors. Allows enrichment (user provides name, parser fills revision). Gracefully degrades when either source is unavailable.
- **Cons:** More complex. Requires reconciliation logic and mismatch handling.

## Decision

**Declared by user + observed from artifact + reconciled by service.**

Five reconciliation outcomes:

| Status | User provided | Parser extracted | Resolution |
|--------|--------------|-----------------|------------|
| `matched` | Yes | Yes, agrees | Use declared |
| `enriched` | Partial | Fills gaps | Merge (declared fields + parser fills) |
| `mismatch` | Yes | Yes, disagrees | Flag strongly; use declared |
| `declared_only` | Yes | Parser failed | Use declared |
| `parsed_only` | No | Yes | Use parsed |

On mismatch: the declared value takes precedence (it's the user's explicit assertion), but the mismatch is flagged for review. This avoids silent acceptance of conflicting provenance.

## Scientific Justification

Software provenance in computational chemistry is not merely metadata — it determines how keywords are interpreted, what defaults apply, and what numerical behavior to expect. The same keyword can have different semantics across versions (e.g., Gaussian's default integration grid changed between versions). Incorrect software attribution can lead to:

- Misinterpretation of parameters when the wrong software version's defaults are assumed.
- Irreproducibility when a user attempts to replicate a calculation with the wrong software.
- Incorrect benchmarking when results are attributed to the wrong method implementation.

The dual-source model follows the principle used in experimental science: measurements are cross-checked against independent sources. The user's declaration is one measurement; the parser's extraction is another. Agreement increases confidence; disagreement triggers investigation.

## Implementation Notes

- **Service:** `app/services/software_reconciliation.py` — pure-computation function, no DB session required
- **Gaussian parser:** Extracts `name`, `version`, `build` (including revision) from the `Gaussian NN: PLATFORM-GNNRevX.YY DD-Mon-YYYY` banner
- **ORCA parser:** Extracts version from the `Program Version X.Y.Z` line
- **Revision extraction:** For Gaussian, the build string `EM64L-G09RevD.01` is decomposed: revision `D.01` extracted via regex, full build string preserved
- **Raw banner:** The original banner text is preserved in the reconciliation result for re-interpretation if parsing logic improves

## Limitations & Future Work

- Only Gaussian and ORCA parsers are implemented. Additional ESS parsers (Molpro, NWChem, QChem, etc.) will follow the same dual-source pattern.
- The reconciliation service does not currently persist the match status or raw banner. A future `calculation_software_validation` table or a field on `calculation` could record reconciliation outcomes for audit.
- Build-string decomposition is Gaussian-specific. A more general approach may be needed for other software that encodes platform/architecture in version strings.

## References

- DR-0006: Three-Layer Calculation Parameter Architecture (software identity derived via FK chain, not duplicated on parameters)
