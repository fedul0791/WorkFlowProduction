"""Persist independent CAD-style canvas objects."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0007_canvas_objects"
down_revision: Union[str, None] = "0006_flexible_workspace"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "canvas_objects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("x", sa.Float(), nullable=False, server_default="0"),
        sa.Column("y", sa.Float(), nullable=False, server_default="0"),
        sa.Column("width", sa.Float(), nullable=False, server_default="180"),
        sa.Column("height", sa.Float(), nullable=False, server_default="100"),
        sa.Column("rotation", sa.Float(), nullable=False, server_default="0"),
        sa.Column("placed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["companies.tenant_id"], name="fk_canvas_objects_tenant"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_canvas_objects_tenant_id"),
    )
    op.create_index("ix_canvas_objects_tenant_active", "canvas_objects", ["tenant_id", "archived_at"])


def downgrade() -> None:
    op.drop_index("ix_canvas_objects_tenant_active", table_name="canvas_objects")
    op.drop_table("canvas_objects")
