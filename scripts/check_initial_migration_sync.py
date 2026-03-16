#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import importlib
import sys
from pathlib import Path
from typing import Iterable


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check that a metadata-driven initial Alembic migration imports the same "
            "model modules as the live SQLAlchemy models package."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root added to sys.path before imports.",
    )
    parser.add_argument(
        "--models-dir",
        default="app/db/models",
        help="Path to the SQLAlchemy model modules, relative to repo root.",
    )
    parser.add_argument(
        "--models-package",
        default="app.db.models",
        help="Python package prefix for the model modules.",
    )
    parser.add_argument(
        "--migration-path",
        default="alembic/versions/d861dfd60891_create_intial_schema.py",
        help="Path to the metadata-driven initial migration, relative to repo root.",
    )
    parser.add_argument(
        "--base-module",
        default="app.db.base",
        help="Module that exports the declarative Base.",
    )
    parser.add_argument(
        "--base-attr",
        default="Base",
        help="Attribute name for the declarative Base inside --base-module.",
    )
    parser.add_argument(
        "--exclude-module",
        action="append",
        default=["common"],
        help="Model module stem to exclude from discovery. Can be passed multiple times.",
    )
    return parser.parse_args()


def _discover_model_modules(
    models_dir: Path, models_package: str, excluded_modules: set[str]
) -> tuple[str, ...]:
    module_names: list[str] = []

    for path in sorted(models_dir.glob("*.py")):
        if path.stem in excluded_modules or path.stem == "__init__":
            continue
        module_names.append(f"{models_package}.{path.stem}")

    return tuple(module_names)


def _extract_string_tuple(module_ast: ast.Module, target_name: str) -> tuple[str, ...]:
    for node in module_ast.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == target_name:
                if not isinstance(node.value, (ast.Tuple, ast.List)):
                    raise ValueError(
                        f"{target_name} must be a tuple or list of module strings."
                    )
                values: list[str] = []
                for item in node.value.elts:
                    if not isinstance(item, ast.Constant) or not isinstance(
                        item.value, str
                    ):
                        raise ValueError(
                            f"{target_name} must contain only string literals."
                        )
                    values.append(item.value)
                return tuple(values)
    raise ValueError(f"Could not find {target_name} in migration.")


def _dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node

    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value

    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))

    return None


def _function_has_call(function_node: ast.FunctionDef, dotted_name: str) -> bool:
    for node in ast.walk(function_node):
        if isinstance(node, ast.Call) and _dotted_name(node.func) == dotted_name:
            return True
    return False


def _get_function(module_ast: ast.Module, function_name: str) -> ast.FunctionDef:
    for node in module_ast.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    raise ValueError(f"Could not find function {function_name} in migration.")


def _load_base(base_module_name: str, base_attr_name: str):
    base_module = importlib.import_module(base_module_name)
    return getattr(base_module, base_attr_name)


def _import_modules(module_names: Iterable[str]) -> None:
    for module_name in module_names:
        importlib.import_module(module_name)


def _format_module_diff(label: str, modules: Iterable[str]) -> str:
    sorted_modules = sorted(modules)
    return f"{label}:\n" + "\n".join(
        f"  - {module_name}" for module_name in sorted_modules
    )


def main() -> int:
    args = _parse_args()

    repo_root = args.repo_root.resolve()
    models_dir = (repo_root / args.models_dir).resolve()
    migration_path = (repo_root / args.migration_path).resolve()
    excluded_modules = set(args.exclude_module)

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if not models_dir.is_dir():
        print(f"Model directory not found: {models_dir}", file=sys.stderr)
        return 2

    if not migration_path.is_file():
        print(f"Migration file not found: {migration_path}", file=sys.stderr)
        return 2

    migration_source = migration_path.read_text(encoding="utf-8")
    migration_ast = ast.parse(migration_source, filename=str(migration_path))

    expected_modules = _discover_model_modules(
        models_dir, args.models_package, excluded_modules
    )
    migration_modules = _extract_string_tuple(migration_ast, "_MODEL_MODULES")

    missing_from_migration = set(expected_modules) - set(migration_modules)
    extra_in_migration = set(migration_modules) - set(expected_modules)

    errors: list[str] = []

    if missing_from_migration:
        errors.append(
            _format_module_diff(
                "Modules missing from _MODEL_MODULES", missing_from_migration
            )
        )

    if extra_in_migration:
        errors.append(
            _format_module_diff(
                "Extra modules listed in _MODEL_MODULES", extra_in_migration
            )
        )

    upgrade_function = _get_function(migration_ast, "upgrade")
    downgrade_function = _get_function(migration_ast, "downgrade")

    if not _function_has_call(upgrade_function, "_load_models"):
        errors.append("upgrade() does not call _load_models().")
    if not _function_has_call(upgrade_function, "Base.metadata.create_all"):
        errors.append("upgrade() does not call Base.metadata.create_all().")
    if not _function_has_call(upgrade_function, "op.get_bind"):
        errors.append("upgrade() does not call op.get_bind().")

    if not _function_has_call(downgrade_function, "_load_models"):
        errors.append("downgrade() does not call _load_models().")
    if not _function_has_call(downgrade_function, "Base.metadata.drop_all"):
        errors.append("downgrade() does not call Base.metadata.drop_all().")
    if not _function_has_call(downgrade_function, "op.get_bind"):
        errors.append("downgrade() does not call op.get_bind().")

    Base = _load_base(args.base_module, args.base_attr)
    table_count_before = len(Base.metadata.tables)
    _import_modules(expected_modules)
    table_count_after = len(Base.metadata.tables)

    if table_count_after == 0:
        errors.append("Importing model modules produced zero tables in Base.metadata.")
    if table_count_after < table_count_before:
        errors.append(
            "Base.metadata lost tables after importing models, which should not happen."
        )

    if errors:
        print("Initial migration sync check failed:", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print(
        "Initial migration sync check passed.\n"
        f"Discovered model modules: {len(expected_modules)}\n"
        f"Metadata tables loaded: {table_count_after}\n"
        f"Migration path: {migration_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
