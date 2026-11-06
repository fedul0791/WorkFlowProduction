"""Enterprise hierarchy, equipment assignment history and audit log."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_enterprise_structure"
down_revision = "0001_infrastructure"
branch_labels = None
depends_on = None

def uuid(): return postgresql.UUID(as_uuid=True)
def common_columns():
    return [sa.Column("id", uuid(), primary_key=True), sa.Column("tenant_id", uuid(), nullable=False), sa.Column("name", sa.String(180), nullable=False), sa.Column("description", sa.Text()), sa.Column("archived_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)]
def upgrade():
    op.create_table("companies",*common_columns(),sa.CheckConstraint("tenant_id = id",name="ck_company_tenant_self"),sa.UniqueConstraint("tenant_id",name="uq_companies_tenant_id"),sa.UniqueConstraint("tenant_id","id",name="uq_company_tenant_id"))
    op.create_table("sites",*common_columns(),sa.ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_sites_tenant"),sa.UniqueConstraint("tenant_id","id",name="uq_sites_tenant_id"))
    op.create_table("departments",*common_columns(),sa.Column("site_id",uuid(),nullable=False),sa.ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_departments_parent"),sa.UniqueConstraint("tenant_id","id",name="uq_departments_tenant_id"))
    op.create_table("areas",*common_columns(),sa.Column("department_id",uuid(),nullable=False),sa.ForeignKeyConstraint(["tenant_id","department_id"],["departments.tenant_id","departments.id"],name="fk_areas_parent"),sa.UniqueConstraint("tenant_id","id",name="uq_areas_tenant_id"))
    op.create_table("workstations",*common_columns(),sa.Column("area_id",uuid(),nullable=False),sa.ForeignKeyConstraint(["tenant_id","area_id"],["areas.tenant_id","areas.id"],name="fk_workstations_parent"),sa.UniqueConstraint("tenant_id","id",name="uq_workstations_tenant_id"))
    op.create_table("equipment",*common_columns(),sa.ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_equipment_tenant"),sa.UniqueConstraint("tenant_id","id",name="uq_equipment_tenant_id"))
    op.create_table("equipment_assignments",sa.Column("id",uuid(),primary_key=True),sa.Column("tenant_id",uuid(),nullable=False),sa.Column("equipment_id",uuid(),nullable=False),sa.Column("workstation_id",uuid(),nullable=False),sa.Column("valid_from",sa.DateTime(timezone=True),nullable=False),sa.Column("valid_to",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.ForeignKeyConstraint(["tenant_id","equipment_id"],["equipment.tenant_id","equipment.id"],name="fk_assignment_equipment"),sa.ForeignKeyConstraint(["tenant_id","workstation_id"],["workstations.tenant_id","workstations.id"],name="fk_assignment_workstation"),sa.CheckConstraint("valid_to IS NULL OR valid_to > valid_from",name="ck_assignment_period"))
    op.create_index("uq_assignment_open_equipment","equipment_assignments",["tenant_id","equipment_id"],unique=True,postgresql_where=sa.text("valid_to IS NULL"))
    op.create_table("audit_events",sa.Column("id",uuid(),primary_key=True),sa.Column("tenant_id",uuid(),nullable=False),sa.Column("actor_id",uuid()),sa.Column("entity_type",sa.String(40),nullable=False),sa.Column("entity_id",uuid(),nullable=False),sa.Column("action",sa.String(40),nullable=False),sa.Column("before_data",postgresql.JSONB()),sa.Column("after_data",postgresql.JSONB()),sa.Column("occurred_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_audit_tenant"))
    op.create_index("ix_audit_tenant_entity","audit_events",["tenant_id","entity_type","entity_id","occurred_at"])
def downgrade():
    op.drop_index("ix_audit_tenant_entity",table_name="audit_events");op.drop_table("audit_events")
    op.drop_index("uq_assignment_open_equipment",table_name="equipment_assignments");op.drop_table("equipment_assignments")
    for table in ("equipment","workstations","areas","departments","sites","companies"): op.drop_table(table)
