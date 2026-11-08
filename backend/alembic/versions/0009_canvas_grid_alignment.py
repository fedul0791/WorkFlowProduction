"""Align existing canvas geometry to the one-metre grid."""
from typing import Sequence, Union

from alembic import op

revision: str = "0009_canvas_grid_alignment"
down_revision: Union[str, None] = "0008_canvas_object_tools"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE canvas_objects
        SET x = round(x / 40) * 40,
            y = round(y / 40) * 40,
            width = greatest(40, round(width / 40) * 40),
            height = greatest(40, round(height / 40) * 40)
        WHERE placed IS TRUE
        """
    )


def downgrade() -> None:
    pass
