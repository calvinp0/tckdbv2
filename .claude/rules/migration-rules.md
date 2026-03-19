# Migration Rules

These rules apply when working with Alembic migrations in `alembic/`.

## Key Facts

- The initial migration (`d861dfd60891`) uses `Base.metadata.create_all()` and seeds `reaction_family` data. Do not modify it without understanding downstream effects.
- Environment variables for the DB connection are read in `alembic/env.py` (`DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_HOST`, `DB_PORT`).
- Tests auto-create a `tckdb_test` database (configurable via `DB_TEST_NAME`), run migrations, and each test rolls back its transaction.

## Before Creating a Migration

1. Ensure the new model module is imported in `app/db/__init__.py`
2. Verify `NAMING_CONVENTION` in `app/db/base.py` is untouched
3. Run `conda run -n tckdb_env alembic check` to see current drift

## After Creating a Migration

1. Review the generated file — check for empty `upgrade()`/`downgrade()`, unintended drops, or naming issues
2. Run `conda run -n tckdb_env alembic upgrade head` to apply
3. Run tests: `conda run -n tckdb_env pytest tests/ -v`
