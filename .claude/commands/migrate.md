---
description: Create and/or run an Alembic migration
argument-hint: "[revision message]"
allowed-tools: ["Bash", "Read", "Edit", "Grep", "Glob"]
---

Manage Alembic migrations for the TCKDB database.

## Behavior

1. **If `$ARGUMENTS` is provided** — create a new migration with that message:
   ```
   conda run -n tckdb_env alembic revision --autogenerate -m "$ARGUMENTS"
   ```
   Then review the generated migration file for correctness (check for empty upgrade/downgrade, dropped columns, naming issues).

2. **If no arguments** — run pending migrations:
   ```
   conda run -n tckdb_env alembic upgrade head
   ```

## Post-migration checks

After either operation:
- Run `conda run -n tckdb_env alembic check` to verify the migration state is clean
- If autogenerate produced an empty migration, warn the user and explain why (model not imported in `app/db/__init__.py`, no actual changes, etc.)

## Critical reminders

- The `NAMING_CONVENTION` in `app/db/base.py` must never be modified
- New model modules must be imported in `app/db/__init__.py` for Alembic discovery
- All enums are centralized in `app/db/models/common.py`
