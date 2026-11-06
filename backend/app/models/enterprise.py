import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Company(Base):
 __tablename__="companies"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False,unique=True)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 allow_multiple_positions:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 allow_multiple_qualifications:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(CheckConstraint("tenant_id = id",name="ck_company_tenant_self"),UniqueConstraint("tenant_id","id",name="uq_company_tenant_id"))

class Site(Base):
 __tablename__="sites"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_sites_tenant"),UniqueConstraint("tenant_id","id",name="uq_sites_tenant_id"))

class Department(Base):
 __tablename__="departments"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 site_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_departments_parent"),UniqueConstraint("tenant_id","id",name="uq_departments_tenant_id"))

class Area(Base):
 __tablename__="areas"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 department_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","department_id"],["departments.tenant_id","departments.id"],name="fk_areas_parent"),UniqueConstraint("tenant_id","id",name="uq_areas_tenant_id"))

class Workstation(Base):
 __tablename__="workstations"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 site_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 department_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 area_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_workstations_site"),ForeignKeyConstraint(["tenant_id","department_id"],["departments.tenant_id","departments.id"],name="fk_workstations_department"),ForeignKeyConstraint(["tenant_id","area_id"],["areas.tenant_id","areas.id"],name="fk_workstations_parent"),CheckConstraint("num_nonnulls(site_id, department_id, area_id) <= 1",name="ck_workstation_location"),UniqueConstraint("tenant_id","id",name="uq_workstations_tenant_id"))

class Equipment(Base):
 __tablename__="equipment"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_equipment_tenant"),UniqueConstraint("tenant_id","id",name="uq_equipment_tenant_id"))

class EquipmentAssignment(Base):
 __tablename__="equipment_assignments"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 equipment_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 site_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 department_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 area_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 workstation_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 valid_to:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","equipment_id"],["equipment.tenant_id","equipment.id"],name="fk_assignment_equipment"),ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_assignment_site"),ForeignKeyConstraint(["tenant_id","department_id"],["departments.tenant_id","departments.id"],name="fk_assignment_department"),ForeignKeyConstraint(["tenant_id","area_id"],["areas.tenant_id","areas.id"],name="fk_assignment_area"),ForeignKeyConstraint(["tenant_id","workstation_id"],["workstations.tenant_id","workstations.id"],name="fk_assignment_workstation"),CheckConstraint("num_nonnulls(site_id, department_id, area_id, workstation_id) <= 1",name="ck_assignment_location"),CheckConstraint("valid_to IS NULL OR valid_to > valid_from",name="ck_assignment_period"),Index("uq_assignment_open_equipment","tenant_id","equipment_id",unique=True,postgresql_where=text("valid_to IS NULL")))

class AuditEvent(Base):
 __tablename__="audit_events"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 actor_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 entity_type:Mapped[str]=mapped_column(String(40),nullable=False)
 entity_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 action:Mapped[str]=mapped_column(String(40),nullable=False)
 before_data:Mapped[dict|None]=mapped_column(JSONB)
 after_data:Mapped[dict|None]=mapped_column(JSONB)
 occurred_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_audit_tenant"),ForeignKeyConstraint(["tenant_id","actor_id"],["users.tenant_id","users.id"],name="fk_audit_actor"),Index("ix_audit_tenant_entity","tenant_id","entity_type","entity_id","occurred_at"))
