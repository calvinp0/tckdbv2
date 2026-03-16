"""create intial schema

Revision ID: d861dfd60891
Revises: 60b67e360daf
Create Date: 2026-03-07 20:04:50.330495

"""

from __future__ import annotations

import importlib
from typing import Sequence, Union

from alembic import op
from app.db.base import Base

# revision identifiers, used by Alembic.
revision: str = "d861dfd60891"
down_revision: Union[str, Sequence[str], None] = "60b67e360daf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MODEL_MODULES = (
    "app.db.models.app_user",
    "app.db.models.author",
    "app.db.models.calculation",
    "app.db.models.geometry",
    "app.db.models.kinetics",
    "app.db.models.level_of_theory",
    "app.db.models.literature",
    "app.db.models.literature_author",
    "app.db.models.network",
    "app.db.models.reaction",
    "app.db.models.software",
    "app.db.models.species",
    "app.db.models.statmech",
    "app.db.models.thermo",
    "app.db.models.transition_state",
    "app.db.models.transport",
    "app.db.models.workflow",
)


def _load_models() -> None:
    for module_name in _MODEL_MODULES:
        importlib.import_module(module_name)


def upgrade() -> None:
    """Upgrade schema."""
    _load_models()
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Downgrade schema."""
    _load_models()
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
