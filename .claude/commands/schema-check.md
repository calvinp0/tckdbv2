---
description: Validate schema changes end-to-end
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
---

Validate that schema changes across models, schemas, and migrations are consistent.

## Steps

1. **Check model imports**: Verify all model modules in `app/db/models/` are imported in `app/db/__init__.py`

2. **Check migration state**: Run `conda run -n tckdb_env alembic check` to detect drift between models and migrations

3. **Cross-reference layers**: For any recently changed models (check `git diff --name-only`):
   - Verify corresponding Pydantic schemas exist in `app/schemas/`
   - Verify upload schemas in `app/schemas/workflows/` don't expose FK IDs
   - Verify read schemas in `app/schemas/entities/` include necessary fields

4. **Run tests**: `conda run -n tckdb_env pytest tests/ -v --tb=short`

5. **Report**: Summarize findings — what's aligned, what's missing or inconsistent
