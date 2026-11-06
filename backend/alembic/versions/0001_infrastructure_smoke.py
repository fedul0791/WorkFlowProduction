"""Infrastructure smoke migration; no business schema is defined yet.

Revision ID: 0001_infrastructure
Revises:
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001_infrastructure"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Record that the database migration pipeline is operational."""


def downgrade() -> None:
    """No application tables exist in this infrastructure-only revision."""
