"""employee contact details and flexible work zones

Revision ID: 0005_employee_contact_and_work_zones
Revises: 0004_employee_work_assignments
Create Date: 2026-11-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_employee_contact_zones"
down_revision: Union[str, None] = "0004_employee_work_assignments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("employees", sa.Column("phone", sa.String(length=40), nullable=True))
    op.add_column("employees", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("employee_work_assignments", sa.Column("department_id", sa.UUID(), nullable=True))
    op.add_column("employee_work_assignments", sa.Column("area_id", sa.UUID(), nullable=True))
    op.create_foreign_key("fk_employee_work_assignments_department", "employee_work_assignments", "departments", ["tenant_id", "department_id"], ["tenant_id", "id"])
    op.create_foreign_key("fk_employee_work_assignments_area", "employee_work_assignments", "areas", ["tenant_id", "area_id"], ["tenant_id", "id"])
    op.create_check_constraint("ck_employee_work_assignment_location", "employee_work_assignments", "num_nonnulls(department_id, area_id, workstation_id) <= 1")


def downgrade() -> None:
    op.drop_constraint("ck_employee_work_assignment_location", "employee_work_assignments", type_="check")
    op.drop_constraint("fk_employee_work_assignments_area", "employee_work_assignments", type_="foreignkey")
    op.drop_constraint("fk_employee_work_assignments_department", "employee_work_assignments", type_="foreignkey")
    op.drop_column("employee_work_assignments", "area_id")
    op.drop_column("employee_work_assignments", "department_id")
    op.drop_column("employees", "address")
    op.drop_column("employees", "phone")
