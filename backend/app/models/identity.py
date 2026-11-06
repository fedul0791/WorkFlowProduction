import uuid
from datetime import datetime
from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class User(Base):
 __tablename__="users"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 email:Mapped[str]=mapped_column(String(320),nullable=False)
 password_hash:Mapped[str]=mapped_column(String(256),nullable=False)
 is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_users_tenant"),UniqueConstraint("tenant_id","id",name="uq_users_tenant_id"),Index("uq_users_email_lower","email",unique=True))
class Employee(Base):
 __tablename__="employees"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 user_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 site_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 employee_number:Mapped[str]=mapped_column(String(40),nullable=False)
 full_name:Mapped[str]=mapped_column(String(240),nullable=False)
 phone:Mapped[str|None]=mapped_column(String(40))
 address:Mapped[str|None]=mapped_column(String(500))
 is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 archived_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_employees_tenant"),ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_employees_site"),ForeignKeyConstraint(["tenant_id","user_id"],["users.tenant_id","users.id"],name="fk_employees_user"),UniqueConstraint("tenant_id","id",name="uq_employees_tenant_id"),UniqueConstraint("tenant_id","employee_number",name="uq_employees_number"),UniqueConstraint("tenant_id","user_id",name="uq_employees_user"))
class EmployeeWorkAssignment(Base):
 __tablename__="employee_work_assignments"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 employee_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 site_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 department_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 area_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 workstation_id:Mapped[uuid.UUID|None]=mapped_column(UUID(as_uuid=True))
 valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 valid_to:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","employee_id"],["employees.tenant_id","employees.id"],name="fk_employee_work_assignments_employee"),ForeignKeyConstraint(["tenant_id","site_id"],["sites.tenant_id","sites.id"],name="fk_employee_work_assignments_site"),ForeignKeyConstraint(["tenant_id","department_id"],["departments.tenant_id","departments.id"],name="fk_employee_work_assignments_department"),ForeignKeyConstraint(["tenant_id","area_id"],["areas.tenant_id","areas.id"],name="fk_employee_work_assignments_area"),ForeignKeyConstraint(["tenant_id","workstation_id"],["workstations.tenant_id","workstations.id"],name="fk_employee_work_assignments_workstation"),CheckConstraint("num_nonnulls(department_id, area_id, workstation_id) <= 1",name="ck_employee_work_assignment_location"),CheckConstraint("valid_to IS NULL OR valid_to > valid_from",name="ck_employee_work_assignment_period"),Index("ix_employee_work_assignments_period","tenant_id","employee_id","valid_from"))
class Position(Base):
 __tablename__="positions"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(160),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_positions_tenant"),UniqueConstraint("tenant_id","id",name="uq_positions_tenant_id"),UniqueConstraint("tenant_id","name",name="uq_positions_name"))
class EmployeePosition(Base):
 __tablename__="employee_positions"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 employee_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 position_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 valid_to:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 __table_args__=(ForeignKeyConstraint(["tenant_id","employee_id"],["employees.tenant_id","employees.id"],name="fk_employee_positions_employee"),ForeignKeyConstraint(["tenant_id","position_id"],["positions.tenant_id","positions.id"],name="fk_employee_positions_position"),CheckConstraint("valid_to IS NULL OR valid_to > valid_from",name="ck_employee_position_period"),Index("uq_employee_position_current","tenant_id","employee_id","position_id",unique=True,postgresql_where=__import__("sqlalchemy").text("valid_to IS NULL")))
class Qualification(Base):
 __tablename__="qualifications"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 name:Mapped[str]=mapped_column(String(180),nullable=False)
 description:Mapped[str|None]=mapped_column(Text)
 is_active:Mapped[bool]=mapped_column(Boolean,nullable=False,default=True,server_default="true")
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_qualifications_tenant"),UniqueConstraint("tenant_id","id",name="uq_qualifications_tenant_id"),UniqueConstraint("tenant_id","name",name="uq_qualifications_name"))
class EmployeeQualification(Base):
 __tablename__="employee_qualifications"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 employee_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 qualification_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 issued_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 expires_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 status:Mapped[str]=mapped_column(String(20),nullable=False,default="active",server_default="active")
 __table_args__=(ForeignKeyConstraint(["tenant_id","employee_id"],["employees.tenant_id","employees.id"],name="fk_employee_qualifications_employee"),ForeignKeyConstraint(["tenant_id","qualification_id"],["qualifications.tenant_id","qualifications.id"],name="fk_employee_qualifications_qualification"),CheckConstraint("status IN ('active','suspended','revoked')",name="ck_employee_qualification_status"),CheckConstraint("expires_at IS NULL OR expires_at > issued_at",name="ck_employee_qualification_period"))
class Role(Base):
 __tablename__="roles"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 code:Mapped[str]=mapped_column(String(60),nullable=False)
 name:Mapped[str]=mapped_column(String(120),nullable=False)
 is_system:Mapped[bool]=mapped_column(Boolean,nullable=False,default=False,server_default="false")
 __table_args__=(ForeignKeyConstraint(["tenant_id"],["companies.tenant_id"],name="fk_roles_tenant"),UniqueConstraint("tenant_id","id",name="uq_roles_tenant_id"),UniqueConstraint("tenant_id","code",name="uq_roles_code"))
class Permission(Base):
 __tablename__="permissions"
 code:Mapped[str]=mapped_column(String(80),primary_key=True)
 description:Mapped[str]=mapped_column(String(240),nullable=False)
class RolePermission(Base):
 __tablename__="role_permissions"
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True)
 role_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True)
 permission_code:Mapped[str]=mapped_column(String(80),primary_key=True)
 __table_args__=(ForeignKeyConstraint(["tenant_id","role_id"],["roles.tenant_id","roles.id"],name="fk_role_permissions_role"),ForeignKeyConstraint(["permission_code"],["permissions.code"],name="fk_role_permissions_permission"))
class UserRole(Base):
 __tablename__="user_roles"
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True)
 user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True)
 role_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True)
 __table_args__=(ForeignKeyConstraint(["tenant_id","user_id"],["users.tenant_id","users.id"],name="fk_user_roles_user"),ForeignKeyConstraint(["tenant_id","role_id"],["roles.tenant_id","roles.id"],name="fk_user_roles_role"))
class UserSession(Base):
 __tablename__="user_sessions"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 user_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 token_hash:Mapped[str]=mapped_column(String(64),nullable=False,unique=True)
 csrf_hash:Mapped[str]=mapped_column(String(64),nullable=False)
 expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 revoked_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now(),nullable=False)
 __table_args__=(ForeignKeyConstraint(["tenant_id","user_id"],["users.tenant_id","users.id"],name="fk_sessions_user"),Index("ix_sessions_expiry","expires_at"))
class EquipmentAuthorization(Base):
 __tablename__="equipment_authorizations"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 employee_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 equipment_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 status:Mapped[str]=mapped_column(String(20),nullable=False,default="active",server_default="active")
 __table_args__=(ForeignKeyConstraint(["tenant_id","employee_id"],["employees.tenant_id","employees.id"],name="fk_equipment_authorizations_employee"),ForeignKeyConstraint(["tenant_id","equipment_id"],["equipment.tenant_id","equipment.id"],name="fk_equipment_authorizations_equipment"),CheckConstraint("expires_at > valid_from",name="ck_equipment_authorization_period"),CheckConstraint("status IN ('active','suspended','revoked')",name="ck_equipment_authorization_status"))
class OperationAuthorization(Base):
 __tablename__="operation_authorizations"
 id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid4)
 tenant_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 employee_id:Mapped[uuid.UUID]=mapped_column(UUID(as_uuid=True),nullable=False)
 operation_code:Mapped[str]=mapped_column(String(80),nullable=False)
 valid_from:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 expires_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),nullable=False)
 status:Mapped[str]=mapped_column(String(20),nullable=False,default="active",server_default="active")
 __table_args__=(ForeignKeyConstraint(["tenant_id","employee_id"],["employees.tenant_id","employees.id"],name="fk_operation_authorizations_employee"),CheckConstraint("expires_at > valid_from",name="ck_operation_authorization_period"),CheckConstraint("status IN ('active','suspended','revoked')",name="ck_operation_authorization_status"))
