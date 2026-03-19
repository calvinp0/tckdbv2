# Schema & Model Rules

These rules apply when editing files in `app/db/models/`, `app/schemas/`, or `schema_spec.md`.

## Critical Invariants

- **`NAMING_CONVENTION` in `app/db/base.py`** must be preserved exactly — it controls constraint/index naming for stable Alembic diffs. Never modify it.
- **All enums** are centralized in `app/db/models/common.py`. Never define enums inline in model files.
- **New model modules** must be imported in `app/db/__init__.py` so Alembic can discover them.
- The `mol` column type (RDKit) is defined as a custom SQLAlchemy type in `app/db/types.py`.

## Design Principles

- **Separation of concerns**: Identity (what something is) vs Result (computed values) vs Provenance (how it was produced) vs Curation (human review/selection).
- **No FK IDs in upload schemas**: Workflow/upload payloads accept scientific content or lookup fragments. FK resolution, deduplication, and parent-child attachment happen in services/workflows, not in user-facing schemas.
- **Read schemas may include IDs** for client consumption.
- **Three-layer resolution**: Upload schema → Workflow orchestration → Resolution helpers.

## Code Style

- SQLAlchemy: explicit `Mapped[...]` and `mapped_column(...)` typing
- ORM classes: `PascalCase`; modules: `snake_case`
