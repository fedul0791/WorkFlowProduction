"""Add canvas object types and geometry locking."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008_canvas_object_tools"
down_revision: Union[str, None] = "0007_canvas_objects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("canvas_objects", sa.Column("object_type", sa.String(80), nullable=False, server_default="custom"))
    op.add_column("canvas_objects", sa.Column("locked", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute("UPDATE canvas_objects SET x = x + 5100, y = y + 3400 WHERE placed IS TRUE")


def downgrade() -> None:
    op.drop_column("canvas_objects", "locked")
    op.drop_column("canvas_objects", "object_type")
