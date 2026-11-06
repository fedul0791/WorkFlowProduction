import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from app.core.security import hash_password,verify_password,token_hash,set_auth_cookies,revoke_session,permissions_for,SESSION_COOKIE,CSRF_COOKIE,get_current_user,require_permission,csrf_protect,audit
from app.db.session import get_db
from app.models import User,UserSession,Role,UserRole,Employee

auth_router=APIRouter(prefix="/api/v1/auth",tags=["authentication"])
admin_router=APIRouter(prefix="/api/v1",tags=["users and access"],dependencies=[Depends(csrf_protect)])
class LoginInput(BaseModel):
 email:str
 password:str=Field(min_length=1,max_length=256)
 @field_validator("email")
 @classmethod
 def valid_email(cls,value):
  import re
  value=value.strip().lower()
  if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value):raise ValueError("Invalid email")
  return value
class UserInput(BaseModel):
 email:str
 password:str=Field(min_length=12,max_length=256)
 employee_id:UUID|None=None
 role_codes:list[str]=Field(min_length=1)
 @field_validator("email")
 @classmethod
 def valid_email(cls,value):
  import re
  value=value.strip().lower()
  if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",value):raise ValueError("Invalid email")
  return value
class ActiveInput(BaseModel):is_active:bool
DUMMY_PASSWORD_HASH=hash_password("This is a fixed dummy authentication password")

class RoleInput(BaseModel):
 code:str=Field(pattern="^[a-z][a-z0-9_-]{2,59}$")
 name:str=Field(min_length=2,max_length=120)

@auth_router.post("/login")
def login(payload:LoginInput,response:Response,request:Request,db:Session=Depends(get_db)):
 origin=request.headers.get("origin")
 from app.core.config import get_settings
 if origin and origin not in [x.strip() for x in get_settings().cors_origins.split(",")]:raise HTTPException(403,"Untrusted origin")
 user=db.scalar(select(User).where(User.email==str(payload.email).lower()))
 valid=verify_password(payload.password,user.password_hash if user else DUMMY_PASSWORD_HASH)
 if not user or not valid or not user.is_active:raise HTTPException(401,"Invalid email or password")
 now=datetime.now(timezone.utc); raw=secrets.token_urlsafe(48);csrf=secrets.token_urlsafe(32)
 session=UserSession(tenant_id=user.tenant_id,user_id=user.id,token_hash=token_hash(raw),csrf_hash=token_hash(csrf),expires_at=now+timedelta(hours=12))
 db.add(session);db.commit()
 set_auth_cookies(response,raw,csrf,get_settings().app_env.lower() not in {"development","dev","test"})
 return {"user":{"id":str(user.id),"email":user.email,"tenant_id":str(user.tenant_id)},"csrf_token":csrf,"expires_at":session.expires_at.isoformat()}
@auth_router.post("/logout",dependencies=[Depends(csrf_protect)])
def logout(response:Response,workflow_session:str|None=__import__("fastapi").Cookie(default=None,alias=SESSION_COOKIE),db:Session=Depends(get_db)):
 revoke_session(db,workflow_session);response.delete_cookie(SESSION_COOKIE,path="/",httponly=True,samesite="strict");response.delete_cookie(CSRF_COOKIE,path="/",samesite="strict");return {"ok":True}
@auth_router.get("/me")
def me(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 roles=db.scalars(select(Role.code,Role.name).join(UserRole,(UserRole.role_id==Role.id)&(UserRole.tenant_id==Role.tenant_id)).where(UserRole.user_id==user.id,UserRole.tenant_id==user.tenant_id)).all()
 return {"id":str(user.id),"email":user.email,"tenant_id":str(user.tenant_id),"roles":[{"code":r[0],"name":r[1]} for r in roles],"permissions":sorted(permissions_for(db,user.id,user.tenant_id))}

@admin_router.get("/users",dependencies=[Depends(require_permission("users:read"))])
def list_users(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 users=db.scalars(select(User).where(User.tenant_id==user.tenant_id).order_by(User.email)).all();out=[]
 for u in users:
  roles=db.scalars(select(Role.code).join(UserRole,(UserRole.role_id==Role.id)&(UserRole.tenant_id==Role.tenant_id)).where(UserRole.user_id==u.id,UserRole.tenant_id==user.tenant_id)).all()
  employee=db.scalar(select(Employee).where(Employee.tenant_id==user.tenant_id,Employee.user_id==u.id))
  out.append({"id":str(u.id),"email":u.email,"is_active":u.is_active,"roles":roles,"employee_id":str(employee.id) if employee else None})
 return out
@admin_router.post("/users",status_code=201,dependencies=[Depends(require_permission("users:write"))])
def create_user(payload:UserInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 email=str(payload.email).lower()
 if db.scalar(select(User.id).where(User.email==email)):raise HTTPException(409,"Email already exists")
 roles=db.scalars(select(Role).where(Role.tenant_id==user.tenant_id,Role.code.in_(payload.role_codes))).all()
 if len(set(payload.role_codes))!=len(payload.role_codes) or len({x.code for x in roles})!=len(set(payload.role_codes)):raise HTTPException(422,"Unknown role for this enterprise")
 employee=None
 if payload.employee_id:
  employee=db.scalar(select(Employee).where(Employee.id==payload.employee_id,Employee.tenant_id==user.tenant_id,Employee.archived_at.is_(None)))
  if not employee or not employee.is_active:raise HTTPException(404,"Active employee not found in this enterprise")
  if employee.user_id:raise HTTPException(409,"Employee already has an account")
 row=User(tenant_id=user.tenant_id,email=email,password_hash=hash_password(payload.password));db.add(row);db.flush()
 for role in roles:db.add(UserRole(tenant_id=user.tenant_id,user_id=row.id,role_id=role.id))
 if employee:employee.user_id=row.id
 audit(db,"user",row.id,"create",after={"email":row.email,"roles":[r.code for r in roles],"employee_id":str(employee.id) if employee else None})
 db.commit();return {"id":str(row.id),"email":row.email,"is_active":row.is_active,"roles":[r.code for r in roles],"employee_id":str(employee.id) if employee else None}
@admin_router.patch("/users/{user_id}/active",dependencies=[Depends(require_permission("users:write"))])
def change_active(user_id:UUID,payload:ActiveInput,actor:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(User).where(User.id==user_id,User.tenant_id==actor.tenant_id))
 if not row:raise HTTPException(404,"User not found")
 if row.id==actor.id and not payload.is_active:raise HTTPException(409,"You cannot deactivate your own account")
 before={"is_active":row.is_active};row.is_active=payload.is_active
 if payload.is_active:
  employee=db.scalar(select(Employee).where(Employee.tenant_id==actor.tenant_id,Employee.user_id==row.id))
  if employee and (not employee.is_active or employee.archived_at):raise HTTPException(409,"Reactivate the employee record before enabling this account")
 if not row.is_active:
  for s in db.scalars(select(UserSession).where(UserSession.tenant_id==actor.tenant_id,UserSession.user_id==row.id,UserSession.revoked_at.is_(None))).all():s.revoked_at=datetime.now(timezone.utc)
 audit(db,"user",row.id,"update",before=before,after={"is_active":row.is_active});db.commit();return {"id":str(row.id),"is_active":row.is_active}
@admin_router.post("/users/{user_id}/archive",dependencies=[Depends(require_permission("users:write"))])
def archive_user(user_id:UUID,actor:User=Depends(get_current_user),db:Session=Depends(get_db)):
 row=db.scalar(select(User).where(User.id==user_id,User.tenant_id==actor.tenant_id))
 if not row:raise HTTPException(404,"User not found")
 is_admin=db.scalar(select(Role.id).join(UserRole,(UserRole.role_id==Role.id)&(UserRole.tenant_id==Role.tenant_id)).where(UserRole.user_id==row.id,UserRole.tenant_id==actor.tenant_id,Role.code=="administrator")) is not None
 if row.is_active and is_admin:
  other_admins=db.scalar(select(func.count(User.id)).join(UserRole,and_(UserRole.user_id==User.id,UserRole.tenant_id==User.tenant_id)).join(Role,and_(Role.id==UserRole.role_id,Role.tenant_id==UserRole.tenant_id)).where(User.tenant_id==actor.tenant_id,User.is_active.is_(True),User.id!=row.id,Role.code=="administrator"))
  if not other_admins:raise HTTPException(409,"The last active administrator cannot be archived")
 if not row.is_active:return {"id":str(row.id),"is_active":False}
 row.is_active=False
 for session in db.scalars(select(UserSession).where(UserSession.tenant_id==actor.tenant_id,UserSession.user_id==row.id,UserSession.revoked_at.is_(None))).all():session.revoked_at=datetime.now(timezone.utc)
 audit(db,"user",row.id,"archive",before={"is_active":True},after={"is_active":False});db.commit()
 return {"id":str(row.id),"is_active":False}
@admin_router.get("/roles",dependencies=[Depends(require_permission("roles:read"))])
def list_roles(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 roles=db.scalars(select(Role).where(Role.tenant_id==user.tenant_id).order_by(Role.code)).all()
 return [{"code":r.code,"name":r.name,"is_system":r.is_system,"permissions":sorted(permissions_for_role(db,user.tenant_id,r.id))} for r in roles]
def permissions_for_role(db,tenant_id,role_id):
 from app.models import RolePermission
 return db.scalars(select(RolePermission.permission_code).where(RolePermission.tenant_id==tenant_id,RolePermission.role_id==role_id)).all()

@admin_router.post("/roles",status_code=201,dependencies=[Depends(require_permission("roles:write"))])
def create_custom_role(payload:RoleInput,user:User=Depends(get_current_user),db:Session=Depends(get_db)):
 if payload.code in {"employee","foreman","director","administrator"}:raise HTTPException(409,"Built-in role codes are reserved")
 if db.scalar(select(Role.id).where(Role.tenant_id==user.tenant_id,Role.code==payload.code)):raise HTTPException(409,"Role code already exists")
 role=Role(tenant_id=user.tenant_id,code=payload.code,name=payload.name.strip(),is_system=False);db.add(role);db.flush();audit(db,"role",role.id,"create",after={"code":role.code,"name":role.name});db.commit();return {"code":role.code,"name":role.name,"is_system":False,"permissions":[]}


