# Literature Policy

This note records the current DOI / ISBN handling policy for TCKDB.

## Goal

If a user provides a valid DOI or ISBN, the backend should be able to:

- normalize the identifier
- fetch metadata from an external source when available
- fill a canonical literature row automatically
- reduce duplicate free-text entries

Manual literature entry is still allowed when no identifier is available.

## Layering

The literature flow is split into three layers.

### Resource Schemas

Resource schemas represent stored literature rows.

- [app/schemas/resources/literature.py](/home/calvin/code/TCKDB_v2/app/schemas/resources/literature.py)

Important shapes:

- `LiteratureCreate`
- `LiteratureUpdate`
- `LiteratureRead`

These are DB-shaped schemas, not upload workflows.

### Workflow Schema

Workflow schemas represent user actions or upload intent.

- [app/schemas/workflows/literature_submission.py](/home/calvin/code/TCKDB_v2/app/schemas/workflows/literature_submission.py)

Important shape:

- `LiteratureSubmissionRequest`

This schema supports both:

- identifier-driven submission via DOI and/or ISBN
- manual fallback submission via `kind` + `title`

### Service Layer

The service layer resolves identifiers, enriches metadata, and creates or reuses rows.

- [app/services/literature_metadata.py](/home/calvin/code/TCKDB_v2/app/services/literature_metadata.py)
- [app/services/literature_resolution.py](/home/calvin/code/TCKDB_v2/app/services/literature_resolution.py)

Important functions:

- `normalize_doi`
- `normalize_isbn`
- `fetch_doi_metadata`
- `fetch_isbn_metadata`
- `resolve_literature_submission`
- `resolve_or_create_literature`

## Identifier Policy

### DOI

Accepted input:

- raw DOI
- `DOI:...`
- `https://doi.org/...`
- `http://doi.org/...`

Stored canonical form:

- lowercase DOI without URL prefix

Example:

- input: `https://doi.org/10.1000/ABC`
- stored: `10.1000/abc`

### ISBN

Accepted input:

- ISBN-10
- ISBN-13
- hyphenated ISBN
- non-hyphenated ISBN

Stored canonical form:

- ISBN-13 without hyphens

Example:

- input: `0-387-95452-X`
- stored: `9780387954523`

Notes:

- ISBN normalization currently uses an `isbnlib`-compatible import path.
- In this repo environment, we install the package with `pip install isbnlib2`.

## Resolution Flow

### DOI-first flow

If DOI is present:

1. normalize DOI
2. look for an existing `literature` row by DOI
3. if found, reuse it
4. if not found, fetch Crossref metadata
5. merge metadata with user fields
6. create a canonical literature row

### ISBN flow

If ISBN is present:

1. normalize to canonical ISBN-13
2. look for an existing `literature` row by ISBN
3. if found, reuse it
4. if not found, fetch book metadata
5. merge metadata with user fields
6. create a canonical literature row

### Manual fallback

If neither DOI nor ISBN is present:

- the request must provide at least `kind` and `title`
- the backend creates a manual literature row without external enrichment

## Merge Policy

Current policy:

- external metadata is used as the default canonical source
- user-provided values fill gaps where fetched metadata is missing

So the merge order is effectively:

- fetched metadata first
- explicit user fields only when fetched fields are absent

This is intentionally conservative for now.

Future alternatives:

- allow explicit user override
- flag mismatches for curator review
- record external metadata provenance separately

## Kind Inference

If `kind` is omitted:

- ISBN implies `LiteratureKind.book`
- DOI implies `LiteratureKind.article`

If neither identifier is present, `kind` must be provided manually.

## What This Improves

This policy is intended to improve:

- user convenience
- metadata standardization
- identifier-based deduplication

In particular, it reduces variation in:

- title capitalization
- journal naming
- publisher naming
- DOI formatting
- ISBN formatting

## Current Limits

Current behavior does not yet:

- create author rows from fetched metadata
- enforce a DB-level unique constraint on DOI or ISBN
- record mismatch/audit decisions between user metadata and fetched metadata

Those can be added later without changing the basic workflow split.
