"""Persist canvas object hierarchy."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010_canvas_object_parent"
down_revision: Union[str, None] = "0009_canvas_grid_alignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("canvas_objects", sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_canvas_objects_parent",
        "canvas_objects",
        "canvas_objects",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_canvas_objects_parent", "canvas_objects", type_="foreignkey")
    op.drop_column("canvas_objects", "parent_id")
