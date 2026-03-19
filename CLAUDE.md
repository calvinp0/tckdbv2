# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCKDB is a Thermochemical and Kinetics Database built with Python, PostgreSQL (with RDKit Cartridge), SQLAlchemy 2.0+, Alembic, and Pydantic v2+. It stores computational chemistry data: species, reactions, transition states, kinetics, thermodynamics, and provenance.

## Common Commands

```bash
# Start local PostgreSQL (RDKit-enabled)
docker compose up -d

# Export DB vars for Alembic
export DB_USER=tckdb DB_PASSWORD=tckdb DB_NAME=tckdb_dev DB_HOST=127.0.0.1 DB_PORT=5432

# Run migrations
conda run -n tckdb_env alembic upgrade head

# Create a new migration
conda run -n tckdb_env alembic revision --autogenerate -m "description"

# Run all tests
conda run -n tckdb_env pytest tests/

# Run a single test file
conda run -n tckdb_env pytest tests/test_reaction_upload.py -v

# Run a specific test
conda run -n tckdb_env pytest tests/test_calculation_resolution.py::test_name -v
```

All commands use the `tckdb_env` conda environment. Tests auto-create a `tckdb_test` database (configurable via `DB_TEST_NAME`), run migrations, and each test rolls back its transaction.

## Architecture

### Layer Responsibilities

| Layer | Location | Role |
|-------|----------|------|
| **ORM models** | `app/db/models/` | SQLAlchemy table definitions only |
| **Schemas** | `app/schemas/` | Pydantic models — `entities/` for read/write, `workflows/` for upload payloads, `fragments/` for reusable pieces |
| **Services** | `app/services/` | Reusable business logic: resolution, deduplication, metadata fetching |
| **Workflows** | `app/workflows/` | Multi-step orchestration (e.g., `persist_reaction_upload`) |
| **Resolution** | `app/resolution/` | Lower-level entity lookup/creation (species, geometry, conformer) |
| **Chemistry** | `app/chemistry/` | Chemistry utility functions |
| **Resources** | `app/resources/` | FastAPI route handlers (reserved, not yet populated) |

<important if="editing app/db/models/ or app/schemas/ or alembic/">
See `.claude/rules/schema-rules.md` for critical invariants, design principles, and code style.
See `.claude/rules/migration-rules.md` for Alembic migration workflow and checks.
</important>

### Database Schema

Documented in `schema_spec.md` (field-level detail) and `schema_analysis.md` (design rationale). Key entity groups:
- **Identity**: `species`, `species_entry`, `chem_reaction`, `reaction_entry`, `transition_state`, `transition_state_entry`
- **Calculations**: `calculation` (hub), `calc_sp_result`, `calc_opt_result`, `calc_freq_result`, input/output geometries, dependencies
- **Conformers**: `conformer_group`, `conformer_observation`, `conformer_assignment_scheme`, `conformer_selection`
- **Scientific products**: `statmech`, `thermo`, `kinetics`, `transport`, `network`
- **Provenance**: `software`/`software_release`, `workflow_tool`/`workflow_tool_release`, `level_of_theory`, `literature`/`author`

## Code Style

- `.editorconfig`: 4-space indent, UTF-8, 120-char soft line limit
- SQLAlchemy: explicit `Mapped[...]` and `mapped_column(...)` typing
- ORM classes: `PascalCase`; modules: `snake_case`

## Key Reference Documents

- `AGENTS.md` — developer guidelines (authoritative for contribution rules)
- `schema_spec.md` — full schema specification
- `literature_policy.md` — DOI/ISBN metadata handling policy
- `species_design.md` — species and conformer design rationale

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **TCKDB_v2** (1661 symbols, 4435 relationships, 36 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## When Debugging

1. `gitnexus_query({query: "<error or symptom>"})` — find execution flows related to the issue
2. `gitnexus_context({name: "<suspect function>"})` — see all callers, callees, and process participation
3. `READ gitnexus://repo/TCKDB_v2/process/{processName}` — trace the full execution flow step by step
4. For regressions: `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` — see what your branch changed

## When Refactoring

- **Renaming**: MUST use `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` first. Review the preview — graph edits are safe, text_search edits need manual review. Then run with `dry_run: false`.
- **Extracting/Splitting**: MUST run `gitnexus_context({name: "target"})` to see all incoming/outgoing refs, then `gitnexus_impact({target: "target", direction: "upstream"})` to find all external callers before moving code.
- After any refactor: run `gitnexus_detect_changes({scope: "all"})` to verify only expected files changed.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/TCKDB_v2/context` | Codebase overview, check index freshness |
| `gitnexus://repo/TCKDB_v2/clusters` | All functional areas |
| `gitnexus://repo/TCKDB_v2/processes` | All execution flows |
| `gitnexus://repo/TCKDB_v2/process/{name}` | Step-by-step execution trace |

## Self-Check Before Finishing

Before completing any code modification task, verify:
1. `gitnexus_impact` was run for all modified symbols
2. No HIGH/CRITICAL risk warnings were ignored
3. `gitnexus_detect_changes()` confirms changes match expected scope
4. All d=1 (WILL BREAK) dependents were updated

## Keeping the Index Fresh

After committing code changes, the GitNexus index becomes stale. Re-run analyze to update it:

```bash
npx gitnexus analyze
```

If the index previously included embeddings, preserve them by adding `--embeddings`:

```bash
npx gitnexus analyze --embeddings
```

To check whether embeddings exist, inspect `.gitnexus/meta.json` — the `stats.embeddings` field shows the count (0 means no embeddings). **Running analyze without `--embeddings` will delete any previously generated embeddings.**

> Claude Code users: A PostToolUse hook handles this automatically after `git commit` and `git merge`.

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
