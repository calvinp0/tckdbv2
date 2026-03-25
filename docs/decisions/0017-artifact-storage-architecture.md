# DR-0017: Calculation Artifact Storage Architecture

**Date:** 2026-03-26
**Status:** Accepted
**Authors:** Calvin

## Context

TCKDB records calculation results (energies, frequencies, convergence) as structured data in the database.  However, the raw output files from electronic structure software (Gaussian `.log`, ORCA `.out`, etc.) are also scientifically valuable: they enable re-parsing with improved parsers, independent verification, and extraction of data not captured in the initial parse.

The question is how to accept, validate, and store these files, given that:
- Uploaders and the TCKDB server may be on different machines.
- Files must be validated before storage (security, integrity, format).
- Storage must be persistent, content-addressable, and eventually scalable to cloud object stores.
- The database schema already has a `calculation_artifact` table with `uri`, `sha256`, `bytes`, and `kind` columns.

## Considered Alternatives

### Alternative A: Store file content as BLOBs in PostgreSQL

- **Description:** Store raw file bytes directly in the database.
- **Pros:** Single system, transactional consistency with calculation records.
- **Cons / why rejected:** Database bloat for large files (Gaussian TS logs can exceed 1 MB).  Backup complexity.  Poor fit for PostgreSQL's strengths.  Mixing structured data with blob storage violates separation of concerns.

### Alternative B: User-supplied URIs (file paths or URLs)

- **Description:** Uploader provides a path or URL; server stores it as-is.
- **Pros:** Simple.  No file transfer.
- **Cons / why rejected:** URIs are meaningless across machines.  No integrity verification.  No content validation.  Server cannot serve the file to other consumers.  Path traversal risk.

### Alternative C: Base64 inline upload with server-side content-addressed S3 storage

- **Description:** Uploader sends file content as base64 in the JSON payload.  Server decodes, validates (ESS signature, SHA-256 integrity, size limits, text encoding), stores in an S3-compatible object store (MinIO locally, AWS S3 in production) using content-addressed keys, and records the final URI in `calculation_artifact`.
- **Pros:** Self-contained payloads.  Server controls storage location.  Content-addressed dedup.  Validated before storage.  S3-compatible = cloud-ready.  Clean separation: transport format (base64) ≠ storage format (S3 object) ≠ DB record (URI + metadata).
- **Cons:** ~33% base64 overhead on upload.  Payload size increases.  Requires S3-compatible service running.

## Decision

Adopt Alternative C: base64 inline upload with server-side S3 content-addressed storage.

### Upload schema (transport only)

`ArtifactIn` carries `content_base64`, `filename`, `kind`, optional `sha256` and `bytes`.  This schema exists only on the upload path — the database model (`CalculationArtifact`) stores `uri`, `sha256`, `bytes`, `kind` with no inline content.

### Validation pipeline

Before storage, every artifact passes through `validate_artifact()`:

1. **Size check:** reject empty files and files exceeding 50 MB.
2. **SHA-256 integrity:** if the uploader declared a hash, verify it matches.
3. **Byte count:** if declared, verify it matches decoded content length.
4. **Text encoding:** `output_log`, `input`, and `formatted_checkpoint` kinds must be valid UTF-8.
5. **ESS signature:** `output_log` artifacts must contain a recognized ESS header in the first 4 KB (Gaussian, ORCA, Q-Chem, Molpro, Psi4, NWChem, Turbomole, CFOUR).

### Storage

Content-addressed keys: `{sha256[:2]}/{sha256}`.  Stored in an S3-compatible bucket (`tckdb-artifacts`).  Deduplication is automatic — same content = same key = single object.

### Configuration

S3 endpoint, credentials, bucket, and region are configured via environment variables (`S3_ENDPOINT_URL`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`, `S3_REGION`), documented in `.env.example`.  Default values match the docker-compose MinIO setup for zero-config local development.

## Scientific Justification

Raw ESS output files are primary scientific data.  In computational chemistry, re-analysis of output files is routine: new thermochemistry schemes, improved frequency scaling factors, or bug fixes in parsers all require access to the original output.  Discarding these files after initial parsing would be a significant loss of scientific value.

Content-addressed storage ensures that:
- The same output file uploaded by different users is stored once (dedup by SHA-256).
- Any stored file can be independently verified against its hash.
- Files are immutable once stored — no silent corruption or modification.

ESS signature validation prevents the storage system from becoming a general-purpose file upload service.  Only recognized computational chemistry output files are accepted, reducing the attack surface without impacting legitimate use.

The separation between transport format (base64 in JSON) and storage format (S3 objects) means the upload protocol can evolve independently from the storage backend.  Moving from MinIO to AWS S3 requires only configuration changes, not code changes.

## Implementation Notes

- **Validation:** `app/services/artifact_storage.py` — `validate_artifact()`, `store_artifact()`, ESS signature constants.
- **Upload schema:** `ArtifactIn` in `app/schemas/workflows/network_pdep_upload.py` — transport-only, not on DB model.
- **Workflow integration:** `_persist_artifact()` in `app/workflows/computed_reaction.py` — decode → validate → store → create DB row.
- **ARC ingestion:** `scripts/arc_ingestion/builder.py` — reads Gaussian logs, base64-encodes, computes SHA-256, attaches as `ArtifactIn`.
- **Docker:** MinIO service in `docker-compose.yml` with named volume `tckdb_minio`.
- **Tests:** `tests/services/test_artifact_storage.py` — 23 tests covering validation (signatures, integrity, size, encoding) and S3 storage (store, dedup, content verification) against real MinIO.

## Limitations & Future Work

- **Base64 overhead** adds ~33% to payload size.  For batch uploads with many large files, multipart upload or staged upload (presigned URLs) would be more efficient.  This is a future optimization.
- **No file retrieval API** yet.  A `GET /artifacts/{sha256}` endpoint to download stored files would be needed for re-analysis workflows.
- **Signature list** is manually maintained.  Adding new ESS software requires updating the `OUTPUT_LOG_SIGNATURES` dict.
- **No virus scanning** or deeper content analysis beyond signature detection and UTF-8 validation.

## References

- DR-0004: Calculation Structure-Level Provenance (calculation → artifact relationship)
- DR-0012: Cross-Software Parser Architecture (ESS output format recognition)
