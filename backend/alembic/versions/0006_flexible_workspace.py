"""Allow shared workspace placements at the company, site, department, area, or workstation level."""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_flexible_workspace"
down_revision: Union[str, None] = "0005_employee_contact_zones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workstations", sa.Column("site_id", sa.UUID(), nullable=True))
    op.add_column("workstations", sa.Column("department_id", sa.UUID(), nullable=True))
    op.alter_column("workstations", "area_id", nullable=True)
    op.create_foreign_key("fk_workstations_site", "workstations", "sites", ["tenant_id", "site_id"], ["tenant_id", "id"])
    op.create_foreign_key("fk_workstations_department", "workstations", "departments", ["tenant_id", "department_id"], ["tenant_id", "id"])
    op.create_check_constraint("ck_workstation_location", "workstations", "num_nonnulls(site_id, department_id, area_id) <= 1")

    op.add_column("equipment_assignments", sa.Column("site_id", sa.UUID(), nullable=True))
    op.add_column("equipment_assignments", sa.Column("department_id", sa.UUID(), nullable=True))
    op.add_column("equipment_assignments", sa.Column("area_id", sa.UUID(), nullable=True))
    op.alter_column("equipment_assignments", "workstation_id", nullable=True)
    op.create_foreign_key("fk_assignment_site", "equipment_assignments", "sites", ["tenant_id", "site_id"], ["tenant_id", "id"])
    op.create_foreign_key("fk_assignment_department", "equipment_assignments", "departments", ["tenant_id", "department_id"], ["tenant_id", "id"])
    op.create_foreign_key("fk_assignment_area", "equipment_assignments", "areas", ["tenant_id", "area_id"], ["tenant_id", "id"])
    op.create_check_constraint("ck_assignment_location", "equipment_assignments", "num_nonnulls(site_id, department_id, area_id, workstation_id) <= 1")

    op.alter_column("employee_work_assignments", "site_id", nullable=True)


def downgrade() -> None:
    op.alter_column("employee_work_assignments", "site_id", nullable=False)
    op.drop_constraint("ck_assignment_location", "equipment_assignments", type_="check")
    op.drop_constraint("fk_assignment_area", "equipment_assignments", type_="foreignkey")
    op.drop_constraint("fk_assignment_department", "equipment_assignments", type_="foreignkey")
    op.drop_constraint("fk_assignment_site", "equipment_assignments", type_="foreignkey")
    op.alter_column("equipment_assignments", "workstation_id", nullable=False)
    op.drop_column("equipment_assignments", "area_id")
    op.drop_column("equipment_assignments", "department_id")
    op.drop_column("equipment_assignments", "site_id")
    op.drop_constraint("ck_workstation_location", "workstations", type_="check")
    op.drop_constraint("fk_workstations_department", "workstations", type_="foreignkey")
    op.drop_constraint("fk_workstations_site", "workstations", type_="foreignkey")
    op.drop_column("workstations", "department_id")
    op.drop_column("workstations", "site_id")
    op.alter_column("workstations", "area_id", nullable=False)
