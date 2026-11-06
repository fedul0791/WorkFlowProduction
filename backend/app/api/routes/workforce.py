from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Employee,EmployeeWorkAssignment,EmployeePosition,Position,Qualification,EmployeeQualification,Equipment,EquipmentAuthorization,OperationAuthorization,Company,Site,Department,Area,Workstation,User,UserSession,Role,RolePermission,UserRole
from app.core.security import get_current_user,require_permission,require_any_permission,csrf_protect,audit,hash_password,permissions_for,PERMISSIONS

router=APIRouter(prefix="/api/v1",tags=["workforce"],dependencies=[Depends(csrf_protect)])
class EmployeeInput(BaseModel):employee_number:str=Field(min_length=1,max_length=40);full_name:str=Field(min_length=2,max_length=240);phone:str|None=Field(default=None,max_length=40);address:str|None=Field(default=None,max_length=500);site_id:UUID|None=None;is_active:bool=True
class EmployeePatch(BaseModel):employee_number:str|None=Field(default=None,min_length=1,max_length=40);full_name:str|None=Field(default=None,min_length=2,max_length=240);phone:str|None=Field(default=None,max_length=40);address:str|None=Field(default=None,max_length=500);site_id:UUID|None=None;is_active:bool|None=None
class NameInput(BaseModel):name:str=Field(min_length=1,max_length=180);description:str|None=None
class PositionInput(NameInput):pass
class QualificationInput(NameInput):pass
class AssignPosition(BaseModel):position_id:UUID;valid_from:datetime|None=None
class AssignQualification(BaseModel):qualification_id:UUID;issued_at:datetime;expires_at:datetime|None=None
class EmployeeWorkAssignmentInput(BaseModel):site_id:UUID|None=None;department_id:UUID|None=None;area_id:UUID|None=None;workstation_id:UUID|None=None;valid_from:datetime;valid_to:datetime|None=None
class EmployeeWorkAssignmentPeriod(BaseModel):valid_to:datetime|None
class AuthorizationInput(BaseModel):employee_id:UUID;equipment_id:UUID|None=None;operation_code:str|None=None;valid_from:datetime;expires_at:datetime
class StatusInput(BaseModel):status:str=Field(pattern="^(active|suspended|revoked)$")
class PermissionList(BaseModel):permissions:list[str]
class UserRolesInput(BaseModel):role_codes:list[str]=Field(min_length=1)

def employee_or_404(db,tenant_id,eid):
 e=db.scalar(select(Employee).where(Employee.id==eid,Employee.tenant_id==tenant_id))
 if not e:raise HTTPException(404,"Employee not found")
 return e
def check_site(db,tenant_id,site_id):
 if site_id and not db.scalar(select(Site.id).where(Site.id==site_id,Site.tenant_id==tenant_id,Site.archived_at.is_(None))):raise HTTPException(404,"Site not found in this enterprise")
def employee_data(e):return {"id":str(e.id),"employee_number":e.employee_number,"full_name":e.full_name,"phone":e.phone,"address":e.address,"site_id":str(e.site_id) if e.site_id else None,"user_id":str(e.user_id) if e.user_id else None,"is_active":e.is_active,"archived_at":e.archived_at.isoformat() if e.archived_at else None}
def require_employee_access(db,user,tenant_id,eid):
 if "employees:read" in permissions_for(db,user.id,tenant_id):return
 if "employees:self" in permissions_for(db,user.id,tenant_id):
  own=db.scalar(select(Employee.id).where(Employee.tenant_id==tenant_id,Employee.user_id==user.id,Employee.id==eid))
  if own:return
 raise HTTPException(403,"Permission denied")

@router.get("/employees",dependencies=[Depends(require_any_permission("employees:read","employees:self"))])
def list_employees(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 q=select(Employee).where(Employee.tenant_id==user.tenant_id,Employee.archived_at.is_(None)).order_by(Employee.full_name)
 if "employees:read" not in permissions_for(db,user.id,user.tenant_id):q=q.where(Employee.user_id==user.id)
 return [employee_data(e) for e in db.scalars(q).all()]
@router.get("/employees/archived",dependencies=[Depends(require_permission("employees:write"))])
def list_archived_employees(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [employee_data(e) for e in db.scalars(select(Employee).where(Employee.tenant_id==user.tenant_id,Employee.archived_at.is_not(None)).order_by(Employee.full_name)).all()]
@router.post("/employees",status_code=201,dependencies=[Depends(require_permission("employees:write"))])
def create_employee(p:EmployeeInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 check_site(db,user.tenant_id,p.site_id)
 row=Employee(tenant_id=user.tenant_id,employee_number=p.employee_number.strip(),full_name=p.full_name.strip(),phone=p.phone.strip() if p.phone else None,address=p.address.strip() if p.address else None,site_id=p.site_id,is_active=p.is_active);db.add(row);db.flush();audit(db,"employee",row.id,"create",after=employee_data(row));db.commit();return employee_data(row)
@router.get("/employees/{eid}",dependencies=[Depends(require_any_permission("employees:read","employees:self"))])
def get_employee(eid:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 require_employee_access(db,user,user.tenant_id,eid);e=employee_or_404(db,user.tenant_id,eid)
 positions=db.scalars(select(EmployeePosition).where(EmployeePosition.tenant_id==user.tenant_id,EmployeePosition.employee_id==e.id).order_by(EmployeePosition.valid_from.desc())).all()
 quals=db.scalars(select(EmployeeQualification).where(EmployeeQualification.tenant_id==user.tenant_id,EmployeeQualification.employee_id==e.id)).all()
 account=db.scalar(select(User).where(User.id==e.user_id,User.tenant_id==user.tenant_id)) if e.user_id else None
 return {**employee_data(e),"account_email":account.email if account else None,"positions":[{"position_id":str(x.position_id),"valid_from":x.valid_from.isoformat(),"valid_to":x.valid_to.isoformat() if x.valid_to else None} for x in positions],"qualifications":[{"id":str(x.id),"qualification_id":str(x.qualification_id),"issued_at":x.issued_at.isoformat(),"expires_at":x.expires_at.isoformat() if x.expires_at else None,"status":x.status} for x in quals]}

def employee_work_assignment_data(row,site_name,workstation_name,department_name=None,area_name=None):
 return {"id":str(row.id),"employee_id":str(row.employee_id),"site_id":str(row.site_id) if row.site_id else None,"site_name":site_name,"department_id":str(row.department_id) if row.department_id else None,"department_name":department_name,"area_id":str(row.area_id) if row.area_id else None,"area_name":area_name,"workstation_id":str(row.workstation_id) if row.workstation_id else None,"workstation_name":workstation_name,"valid_from":row.valid_from.isoformat(),"valid_to":row.valid_to.isoformat() if row.valid_to else None,"created_at":row.created_at.isoformat() if row.created_at else None}

@router.get("/employees/{eid}/work-assignments",dependencies=[Depends(require_any_permission("employees:read","employees:self"))])
def list_employee_work_assignments(eid:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 require_employee_access(db,user,user.tenant_id,eid)
 rows=db.execute(select(EmployeeWorkAssignment,Site.name,Workstation.name,Department.name,Area.name).outerjoin(Site,and_(Site.id==EmployeeWorkAssignment.site_id,Site.tenant_id==EmployeeWorkAssignment.tenant_id)).outerjoin(Workstation,and_(Workstation.id==EmployeeWorkAssignment.workstation_id,Workstation.tenant_id==EmployeeWorkAssignment.tenant_id)).outerjoin(Department,and_(Department.id==EmployeeWorkAssignment.department_id,Department.tenant_id==EmployeeWorkAssignment.tenant_id)).outerjoin(Area,and_(Area.id==EmployeeWorkAssignment.area_id,Area.tenant_id==EmployeeWorkAssignment.tenant_id)).where(EmployeeWorkAssignment.tenant_id==user.tenant_id,EmployeeWorkAssignment.employee_id==eid).order_by(EmployeeWorkAssignment.valid_from.desc())).all()
 return [employee_work_assignment_data(row,site_name,workstation_name,department_name,area_name) for row,site_name,workstation_name,department_name,area_name in rows]

@router.post("/employees/{eid}/work-assignments",status_code=201,dependencies=[Depends(require_permission("employees:write"))])
def create_employee_work_assignment(eid:UUID,p:EmployeeWorkAssignmentInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 employee=employee_or_404(db,user.tenant_id,eid)
 if p.valid_to and p.valid_to<=p.valid_from:raise HTTPException(422,"Assignment end must follow its start")
 if sum(value is not None for value in (p.department_id,p.area_id,p.workstation_id))>1:raise HTTPException(422,"Choose only one work zone")
 site=db.scalar(select(Site).where(Site.id==p.site_id,Site.tenant_id==user.tenant_id,Site.archived_at.is_(None))) if p.site_id else None
 if p.site_id and not site:raise HTTPException(404,"Active site not found in this enterprise")
 workstation_name=department_name=area_name=None
 if p.department_id:
  department=db.scalar(select(Department).where(Department.id==p.department_id,Department.tenant_id==user.tenant_id,Department.archived_at.is_(None)))
  if not department or (site and department.site_id!=site.id):raise HTTPException(422,"Department must be active and belong to the selected site")
  site=db.scalar(select(Site).where(Site.id==department.site_id,Site.tenant_id==user.tenant_id,Site.archived_at.is_(None)))
  department_name=department.name
 if p.area_id:
  area_row=db.execute(select(Area,Department.name).join(Department,and_(Department.id==Area.department_id,Department.tenant_id==Area.tenant_id)).where(Area.id==p.area_id,Area.tenant_id==user.tenant_id,Area.archived_at.is_(None),Department.archived_at.is_(None))).first()
  if not area_row:raise HTTPException(422,"Area must be active and belong to this enterprise")
  area_site=db.scalar(select(Site).join(Department,Department.site_id==Site.id).where(Department.id==area_row[0].department_id,Site.tenant_id==user.tenant_id,Site.archived_at.is_(None)))
  if not area_site:raise HTTPException(422,"Area must belong to an active site")
  if site and area_site.id!=site.id:raise HTTPException(422,"Area must belong to the selected site")
  site=area_site
  area_name=area_row[0].name;department_name=area_row[1]
 if p.workstation_id:
  workstation_row=db.execute(select(Workstation,Site).outerjoin(Area,and_(Area.id==Workstation.area_id,Area.tenant_id==Workstation.tenant_id)).outerjoin(Department,and_(Department.id==func.coalesce(Workstation.department_id,Area.department_id),Department.tenant_id==Workstation.tenant_id)).outerjoin(Site,and_(Site.id==func.coalesce(Workstation.site_id,Department.site_id),Site.tenant_id==Workstation.tenant_id)).where(Workstation.id==p.workstation_id,Workstation.tenant_id==user.tenant_id,Workstation.archived_at.is_(None))).first()
  if not workstation_row:raise HTTPException(422,"Workstation must be active and belong to the selected site")
  workstation_name=workstation_row[0].name
  ws_site=workstation_row[1]
  if site and (not ws_site or site.id!=ws_site.id):raise HTTPException(422,"Workstation must belong to the selected site")
  site=ws_site
 if p.area_id and not site:raise HTTPException(422,"Area site could not be resolved")
 if p.workstation_id and not site and (p.site_id or p.department_id or p.area_id):raise HTTPException(422,"Workstation site could not be resolved")
 row=EmployeeWorkAssignment(tenant_id=user.tenant_id,employee_id=employee.id,site_id=site.id if site else None,department_id=p.department_id,area_id=p.area_id,workstation_id=p.workstation_id,valid_from=p.valid_from,valid_to=p.valid_to)
 db.add(row);db.flush()
 after=employee_work_assignment_data(row,site.name if site else None,workstation_name,department_name,area_name)
 audit(db,"employee_work_assignment",row.id,"assign",after=after);db.commit()
 return after

@router.patch("/employee-work-assignments/{assignment_id}/period",dependencies=[Depends(require_permission("employees:write"))])
def update_employee_work_assignment_period(assignment_id:UUID,p:EmployeeWorkAssignmentPeriod,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(EmployeeWorkAssignment).where(EmployeeWorkAssignment.id==assignment_id,EmployeeWorkAssignment.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Work assignment not found")
 if p.valid_to and p.valid_to<=row.valid_from:raise HTTPException(422,"Assignment end must follow its start")
 before={"valid_from":row.valid_from.isoformat(),"valid_to":row.valid_to.isoformat() if row.valid_to else None}
 row.valid_to=p.valid_to
 after={"valid_from":row.valid_from.isoformat(),"valid_to":row.valid_to.isoformat() if row.valid_to else None}
 audit(db,"employee_work_assignment",row.id,"period",before=before,after=after);db.commit()
 return {"id":str(row.id),**after}
@router.patch("/employees/{eid}",dependencies=[Depends(require_permission("employees:write"))])
def patch_employee(eid:UUID,p:EmployeePatch,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 e=employee_or_404(db,user.tenant_id,eid);before=employee_data(e);values=p.model_dump(exclude_unset=True);check_site(db,user.tenant_id,values.get("site_id",e.site_id))
 for k,v in values.items():setattr(e,k,v.strip() if k in {"employee_number","full_name","phone","address"} and v else v)
 if values.get("is_active") is False and e.user_id:
  account=db.scalar(select(User).where(User.id==e.user_id,User.tenant_id==user.tenant_id))
  if account and account.is_active:
   account.is_active=False
   for session in db.scalars(select(UserSession).where(UserSession.tenant_id==user.tenant_id,UserSession.user_id==account.id,UserSession.revoked_at.is_(None))).all():session.revoked_at=datetime.now(timezone.utc)
   audit(db,"user",account.id,"deactivate_with_employee",before={"is_active":True},after={"is_active":False})
 audit(db,"employee",e.id,"update",before=before,after=employee_data(e));db.commit();return employee_data(e)
@router.post("/employees/{eid}/archive",dependencies=[Depends(require_permission("employees:write"))])
def archive_employee(eid:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 e=employee_or_404(db,user.tenant_id,eid)
 if e.archived_at:return employee_data(e)
 before=employee_data(e);e.archived_at=datetime.now(timezone.utc);e.is_active=False
 if e.user_id:
  account=db.scalar(select(User).where(User.id==e.user_id,User.tenant_id==user.tenant_id));account.is_active=False
  audit(db,"user",account.id,"deactivate_with_employee_archive",before={"is_active":True},after={"is_active":False})
  for s in db.scalars(select(UserSession).where(UserSession.tenant_id==user.tenant_id,UserSession.user_id==account.id,UserSession.revoked_at.is_(None))).all():s.revoked_at=datetime.now(timezone.utc)
 audit(db,"employee",e.id,"archive",before=before,after=employee_data(e));db.commit();return employee_data(e)
@router.post("/employees/{eid}/restore",dependencies=[Depends(require_permission("employees:write"))])
def restore_employee(eid:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 e=employee_or_404(db,user.tenant_id,eid)
 if not e.archived_at:raise HTTPException(409,"Employee is already active")
 before=employee_data(e);e.archived_at=None;e.is_active=True;audit(db,"employee",e.id,"restore",before=before,after=employee_data(e));db.commit();return employee_data(e)

@router.get("/positions",dependencies=[Depends(require_permission("positions:read"))])
def list_positions(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [{"id":str(p.id),"name":p.name,"description":p.description,"is_active":p.is_active} for p in db.scalars(select(Position).where(Position.tenant_id==user.tenant_id,Position.is_active.is_(True)).order_by(Position.name)).all()]
@router.get("/positions/archived",dependencies=[Depends(require_permission("positions:write"))])
def list_archived_positions(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [{"id":str(p.id),"name":p.name,"description":p.description} for p in db.scalars(select(Position).where(Position.tenant_id==user.tenant_id,Position.is_active.is_(False)).order_by(Position.name)).all()]
@router.post("/positions",status_code=201,dependencies=[Depends(require_permission("positions:write"))])
def create_position(p:PositionInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=Position(tenant_id=user.tenant_id,name=p.name.strip(),description=p.description);db.add(row);db.flush();audit(db,"position",row.id,"create",after={"name":row.name,"description":row.description});db.commit();return {"id":str(row.id),"name":row.name,"description":row.description,"is_active":row.is_active}
@router.post("/positions/{position_id}/archive",dependencies=[Depends(require_permission("positions:write"))])
def archive_position(position_id:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(Position).where(Position.id==position_id,Position.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Position not found")
 if row.is_active:row.is_active=False;audit(db,"position",row.id,"archive",before={"is_active":True},after={"is_active":False});db.commit()
 return {"id":str(row.id),"is_active":row.is_active}
@router.post("/positions/{position_id}/restore",dependencies=[Depends(require_permission("positions:write"))])
def restore_position(position_id:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(Position).where(Position.id==position_id,Position.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Position not found")
 row.is_active=True;audit(db,"position",row.id,"restore",after={"is_active":True});db.commit();return {"id":str(row.id),"is_active":True}
@router.get("/qualifications",dependencies=[Depends(require_permission("qualifications:read"))])
def list_qualifications(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [{"id":str(q.id),"name":q.name,"description":q.description,"is_active":q.is_active} for q in db.scalars(select(Qualification).where(Qualification.tenant_id==user.tenant_id,Qualification.is_active.is_(True)).order_by(Qualification.name)).all()]
@router.get("/qualifications/archived",dependencies=[Depends(require_permission("qualifications:write"))])
def list_archived_qualifications(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 return [{"id":str(q.id),"name":q.name,"description":q.description} for q in db.scalars(select(Qualification).where(Qualification.tenant_id==user.tenant_id,Qualification.is_active.is_(False)).order_by(Qualification.name)).all()]
@router.post("/qualifications",status_code=201,dependencies=[Depends(require_permission("qualifications:write"))])
def create_qualification(p:QualificationInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=Qualification(tenant_id=user.tenant_id,name=p.name.strip(),description=p.description);db.add(row);db.flush();audit(db,"qualification",row.id,"create",after={"name":row.name,"description":row.description});db.commit();return {"id":str(row.id),"name":row.name,"description":row.description,"is_active":row.is_active}
@router.post("/qualifications/{qualification_id}/archive",dependencies=[Depends(require_permission("qualifications:write"))])
def archive_qualification(qualification_id:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(Qualification).where(Qualification.id==qualification_id,Qualification.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Qualification not found")
 if row.is_active:row.is_active=False;audit(db,"qualification",row.id,"archive",before={"is_active":True},after={"is_active":False});db.commit()
 return {"id":str(row.id),"is_active":row.is_active}
@router.post("/qualifications/{qualification_id}/restore",dependencies=[Depends(require_permission("qualifications:write"))])
def restore_qualification(qualification_id:UUID,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(Qualification).where(Qualification.id==qualification_id,Qualification.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Qualification not found")
 row.is_active=True;audit(db,"qualification",row.id,"restore",after={"is_active":True});db.commit();return {"id":str(row.id),"is_active":True}
@router.post("/employees/{eid}/positions",status_code=201,dependencies=[Depends(require_permission("employees:write"))])
def assign_position(eid:UUID,p:AssignPosition,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 emp=employee_or_404(db,user.tenant_id,eid);pos=db.scalar(select(Position).where(Position.id==p.position_id,Position.tenant_id==user.tenant_id,Position.is_active.is_(True)))
 if not pos:raise HTTPException(404,"Position not found")
 company=db.get(Company,user.tenant_id);now=p.valid_from or datetime.now(timezone.utc)
 if not company.allow_multiple_positions:
  for old in db.scalars(select(EmployeePosition).where(EmployeePosition.tenant_id==user.tenant_id,EmployeePosition.employee_id==eid,EmployeePosition.valid_to.is_(None))).all():
   if now<=old.valid_from:raise HTTPException(422,"New position must start after the current one")
   old.valid_to=now
 row=EmployeePosition(tenant_id=user.tenant_id,employee_id=emp.id,position_id=pos.id,valid_from=now);db.add(row);db.flush();audit(db,"employee_position",row.id,"assign",after={"employee_id":str(eid),"position_id":str(pos.id),"valid_from":now.isoformat()});db.commit();return {"id":str(row.id),"position_id":str(pos.id),"valid_from":now.isoformat()}
@router.post("/employees/{eid}/qualifications",status_code=201,dependencies=[Depends(require_permission("qualifications:write"))])
def assign_qualification(eid:UUID,p:AssignQualification,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 emp=employee_or_404(db,user.tenant_id,eid);qual=db.scalar(select(Qualification).where(Qualification.id==p.qualification_id,Qualification.tenant_id==user.tenant_id,Qualification.is_active.is_(True)))
 if not qual:raise HTTPException(404,"Qualification not found")
 if p.expires_at and p.expires_at<=p.issued_at:raise HTTPException(422,"Expiry must follow issue date")
 company=db.get(Company,user.tenant_id)
 if not company.allow_multiple_qualifications:
  active=db.scalar(select(EmployeeQualification.id).where(EmployeeQualification.tenant_id==user.tenant_id,EmployeeQualification.employee_id==eid,EmployeeQualification.status=="active",(EmployeeQualification.expires_at.is_(None))|(EmployeeQualification.expires_at>p.issued_at)))
  if active:raise HTTPException(409,"Enterprise settings allow only one current qualification")
 row=EmployeeQualification(tenant_id=user.tenant_id,employee_id=emp.id,qualification_id=qual.id,issued_at=p.issued_at,expires_at=p.expires_at);db.add(row);db.flush();audit(db,"employee_qualification",row.id,"assign",after={"employee_id":str(eid),"qualification_id":str(qual.id),"issued_at":p.issued_at.isoformat(),"expires_at":p.expires_at.isoformat() if p.expires_at else None,"status":row.status});db.commit();return {"id":str(row.id),"qualification_id":str(qual.id),"issued_at":p.issued_at.isoformat(),"expires_at":p.expires_at.isoformat() if p.expires_at else None,"status":row.status}
@router.patch("/employee-qualifications/{assignment_id}/status",dependencies=[Depends(require_permission("qualifications:write"))])
def set_qualification_status(assignment_id:UUID,p:StatusInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(EmployeeQualification).where(EmployeeQualification.id==assignment_id,EmployeeQualification.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Assignment not found")
 before={"status":row.status};row.status=p.status;audit(db,"employee_qualification",row.id,"status",before=before,after={"status":row.status});db.commit();return {"id":str(row.id),"status":row.status}

@router.post("/authorizations/equipment",status_code=201,dependencies=[Depends(require_permission("authorizations:write"))])
def grant_equipment_authorization(p:AuthorizationInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 if not p.equipment_id or p.operation_code:raise HTTPException(422,"equipment_id is required")
 emp=employee_or_404(db,user.tenant_id,p.employee_id);eq=db.scalar(select(Equipment).where(Equipment.id==p.equipment_id,Equipment.tenant_id==user.tenant_id,Equipment.archived_at.is_(None)))
 if not eq:raise HTTPException(404,"Equipment not found")
 if p.expires_at<=p.valid_from:raise HTTPException(422,"Expiry must follow start")
 row=EquipmentAuthorization(tenant_id=user.tenant_id,employee_id=emp.id,equipment_id=eq.id,valid_from=p.valid_from,expires_at=p.expires_at);db.add(row);db.flush();audit(db,"equipment_authorization",row.id,"grant",after={"employee_id":str(emp.id),"equipment_id":str(eq.id),"valid_from":p.valid_from.isoformat(),"expires_at":p.expires_at.isoformat(),"status":row.status});db.commit();return {"id":str(row.id),"status":row.status}
@router.post("/authorizations/operation",status_code=201,dependencies=[Depends(require_permission("authorizations:write"))])
def grant_operation_authorization(p:AuthorizationInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 if not p.operation_code or p.equipment_id:raise HTTPException(422,"operation_code is required")
 emp=employee_or_404(db,user.tenant_id,p.employee_id)
 if p.expires_at<=p.valid_from:raise HTTPException(422,"Expiry must follow start")
 row=OperationAuthorization(tenant_id=user.tenant_id,employee_id=emp.id,operation_code=p.operation_code.strip(),valid_from=p.valid_from,expires_at=p.expires_at);db.add(row);db.flush();audit(db,"operation_authorization",row.id,"grant",after={"employee_id":str(emp.id),"operation_code":row.operation_code,"valid_from":p.valid_from.isoformat(),"expires_at":p.expires_at.isoformat(),"status":row.status});db.commit();return {"id":str(row.id),"status":row.status}
@router.get("/authorizations",dependencies=[Depends(require_any_permission("authorizations:read","authorizations:self"))])
def list_authorizations(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 own_only="authorizations:read" not in permissions_for(db,user.id,user.tenant_id);emp=db.scalar(select(Employee).where(Employee.tenant_id==user.tenant_id,Employee.user_id==user.id)) if own_only else None
 eq=select(EquipmentAuthorization).where(EquipmentAuthorization.tenant_id==user.tenant_id);op=select(OperationAuthorization).where(OperationAuthorization.tenant_id==user.tenant_id)
 if own_only:
  if not emp:return {"equipment":[],"operations":[]}
  eq=eq.where(EquipmentAuthorization.employee_id==emp.id);op=op.where(OperationAuthorization.employee_id==emp.id)
 return {"equipment":[{"id":str(x.id),"employee_id":str(x.employee_id),"equipment_id":str(x.equipment_id),"valid_from":x.valid_from.isoformat(),"expires_at":x.expires_at.isoformat(),"status":"expired" if x.expires_at<=datetime.now(timezone.utc) and x.status=="active" else x.status} for x in db.scalars(eq).all()],"operations":[{"id":str(x.id),"employee_id":str(x.employee_id),"operation_code":x.operation_code,"valid_from":x.valid_from.isoformat(),"expires_at":x.expires_at.isoformat(),"status":"expired" if x.expires_at<=datetime.now(timezone.utc) and x.status=="active" else x.status} for x in db.scalars(op).all()]}
@router.patch("/authorizations/{kind}/{authorization_id}/status",dependencies=[Depends(require_permission("authorizations:write"))])
def set_authorization_status(kind:str,authorization_id:UUID,p:StatusInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 model=EquipmentAuthorization if kind=="equipment" else OperationAuthorization if kind=="operation" else None
 if not model:raise HTTPException(404,"Unknown authorization type")
 row=db.scalar(select(model).where(model.id==authorization_id,model.tenant_id==user.tenant_id))
 if not row:raise HTTPException(404,"Authorization not found")
 before={"status":row.status};row.status=p.status;audit(db,f"{kind}_authorization",row.id,"status",before=before,after={"status":row.status});db.commit();return {"id":str(row.id),"status":row.status}

@router.patch("/users/{uid}/roles",dependencies=[Depends(require_permission("roles:write"))])
def replace_user_roles(uid:UUID,p:UserRolesInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 target=db.scalar(select(User).where(User.id==uid,User.tenant_id==user.tenant_id))
 if not target:raise HTTPException(404,"User not found")
 roles=db.scalars(select(Role).where(Role.tenant_id==user.tenant_id,Role.code.in_(p.role_codes))).all()
 if len(set(p.role_codes))!=len(p.role_codes) or len({r.code for r in roles})!=len(set(p.role_codes)):raise HTTPException(422,"Unknown role")
 before=db.scalars(select(Role.code).join(UserRole,UserRole.role_id==Role.id).where(UserRole.tenant_id==user.tenant_id,UserRole.user_id==uid)).all()
 db.query(UserRole).filter(UserRole.tenant_id==user.tenant_id,UserRole.user_id==uid).delete(synchronize_session=False)
 for role in roles:db.add(UserRole(tenant_id=user.tenant_id,user_id=uid,role_id=role.id))
 audit(db,"user",uid,"roles",before={"roles":before},after={"roles":p.role_codes});db.commit();return {"id":str(uid),"roles":p.role_codes}
@router.put("/roles/{role_code}/permissions",dependencies=[Depends(require_permission("roles:write"))])
def update_role_permissions(role_code:str,p:PermissionList,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 role=db.scalar(select(Role).where(Role.tenant_id==user.tenant_id,Role.code==role_code))
 if not role:raise HTTPException(404,"Role not found")
 if set(p.permissions)-set(PERMISSIONS):raise HTTPException(422,"Unknown permission")
 old=db.scalars(select(RolePermission.permission_code).where(RolePermission.tenant_id==user.tenant_id,RolePermission.role_id==role.id)).all()
 db.query(RolePermission).filter(RolePermission.tenant_id==user.tenant_id,RolePermission.role_id==role.id).delete(synchronize_session=False)
 for code in set(p.permissions):db.add(RolePermission(tenant_id=user.tenant_id,role_id=role.id,permission_code=code))
 audit(db,"role",role.id,"permissions",before={"permissions":old},after={"permissions":p.permissions});db.commit();return {"code":role.code,"permissions":p.permissions}

@router.get("/sites",dependencies=[Depends(require_permission("structure:read"))])
def list_sites(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 from app.models import Site
 return [{"id":str(x.id),"name":x.name} for x in db.scalars(select(Site).where(Site.tenant_id==user.tenant_id,Site.archived_at.is_(None)).order_by(Site.name)).all()]
@router.get("/audit",dependencies=[Depends(require_permission("audit:read"))])
def list_audit(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 from app.models import AuditEvent
 rows=db.scalars(select(AuditEvent).where(AuditEvent.tenant_id==user.tenant_id).order_by(AuditEvent.occurred_at.desc()).limit(250)).all()
 return [{"id":str(x.id),"actor_id":str(x.actor_id) if x.actor_id else None,"entity_type":x.entity_type,"entity_id":str(x.entity_id),"action":x.action,"before":x.before_data,"after":x.after_data,"occurred_at":x.occurred_at.isoformat()} for x in rows]
