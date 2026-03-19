---
name: clean-run-db
description: "Drop and reinitialize the database with fresh Alembic migrations. Use when schema changes require a clean slate or when the DB is in a broken state."
user-invocable: true
allowed-tools: ["Bash", "Read", "Write"]
---

When dropping and re-initializing the database:

1. **Backup**: Make a backup of the current database to ensure we don't lose anything. Name backups with the date suffix. If a backup exists that day, append `_[Number]`.
   ```
   conda run -n tckdb_env pg_dump -U tckdb tckdb_dev > backup_tckdb_dev_YYYY-MM-DD.sql
   ```

2. **Note Tables**: Make note of the current DB tables, relationships, and constraints before dropping.

3. **Drop DB**: After backing up, drop the current database tables:
   ```
   conda run -n tckdb_env python -c "from app.db.base import Base, engine; Base.metadata.drop_all(engine)"
   ```

4. **Re-init DB**: Once cleanly dropped, re-run Alembic to put in the new tables:
   ```
   conda run -n tckdb_env alembic upgrade head
   ```

5. **Comparison**: In a running markdown log, provide a succinct comparison of the changes in the new DB vs the one just dropped. When this skill is used and the log exists, append a new comparison section with a clear separator to distinguish between runs.

## Gotchas

- Always verify Docker is running (`docker compose ps`) before attempting DB operations
- The `reaction_family` seed data is applied by the initial migration — verify it was seeded after re-init
- If Alembic fails, check that all models are imported in `app/db/__init__.py`
