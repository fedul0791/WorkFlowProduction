"""employee work assignments

Revision ID: 0004_employee_work_assignments
Revises: a13bfe8d4e7e
Create Date: 2026-11-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_employee_work_assignments"
down_revision: Union[str, None] = "a13bfe8d4e7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee_work_assignments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("employee_id", sa.UUID(), nullable=False),
        sa.Column("site_id", sa.UUID(), nullable=False),
        sa.Column("workstation_id", sa.UUID(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valid_to IS NULL OR valid_to > valid_from", name="ck_employee_work_assignment_period"),
        sa.ForeignKeyConstraint(["tenant_id", "employee_id"], ["employees.tenant_id", "employees.id"], name="fk_employee_work_assignments_employee"),
        sa.ForeignKeyConstraint(["tenant_id", "site_id"], ["sites.tenant_id", "sites.id"], name="fk_employee_work_assignments_site"),
        sa.ForeignKeyConstraint(["tenant_id", "workstation_id"], ["workstations.tenant_id", "workstations.id"], name="fk_employee_work_assignments_workstation"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_employee_work_assignments_period", "employee_work_assignments", ["tenant_id", "employee_id", "valid_from"])


def downgrade() -> None:
    op.drop_index("ix_employee_work_assignments_period", table_name="employee_work_assignments")
    op.drop_table("employee_work_assignments")
