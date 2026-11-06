import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Cookie, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, UserSession, UserRole, Role, RolePermission, Employee

SESSION_COOKIE="workflow_session"
CSRF_COOKIE="workflow_csrf"
SESSION_HOURS=12
ROLE_PERMISSIONS={
 "employee":{"structure:read","employees:self","authorizations:self"},
 "foreman":{"structure:read","employees:read","employees:write","positions:read","qualifications:read","qualifications:write","authorizations:read","authorizations:write"},
 "director":{"structure:read","employees:read","employees:write","positions:read","positions:write","qualifications:read","qualifications:write","authorizations:read","authorizations:write","users:read","roles:read","audit:read"},
 "administrator":{"structure:read","structure:write","employees:read","employees:write","positions:read","positions:write","qualifications:read","qualifications:write","authorizations:read","authorizations:write","users:read","users:write","roles:read","roles:write","audit:read"},
}
ROLE_NAMES={"employee":"Mitarbeiter","foreman":"Meister","director":"Geschäftsführer","administrator":"Administrator"}
PERMISSIONS={"structure:read":"View enterprise structure","structure:write":"Change enterprise structure","employees:self":"View own employee record","employees:read":"View employees","employees:write":"Manage employees","positions:read":"View positions","positions:write":"Manage positions","qualifications:read":"View qualifications","qualifications:write":"Manage qualifications","authorizations:self":"View own authorizations","authorizations:read":"View authorizations","authorizations:write":"Manage authorizations","users:read":"View user accounts","users:write":"Manage user accounts","roles:read":"View roles","roles:write":"Manage roles and permissions","audit:read":"View audit records"}

class CredentialsError(HTTPException): pass

def hash_password(password:str)->str:
 if len(password)<12 or len(password)>256: raise HTTPException(422,"Password must contain 12 to 256 characters")
 salt=secrets.token_bytes(16); digest=hashlib.scrypt(password.encode(),salt=salt,n=16384,r=8,p=1,dklen=32,maxmem=64*1024*1024)
 return "scrypt$16384$8$1$"+base64.urlsafe_b64encode(salt).decode()+"$"+base64.urlsafe_b64encode(digest).decode()
def verify_password(password:str,stored:str)->bool:
 try:
  algo,n,r,p,salt,digest=stored.split("$")
  if algo!="scrypt":return False
  actual=hashlib.scrypt(password.encode(),salt=base64.urlsafe_b64decode(salt),n=int(n),r=int(r),p=int(p),dklen=32,maxmem=64*1024*1024)
  return hmac.compare_digest(actual,base64.urlsafe_b64decode(digest))
 except (ValueError,TypeError):return False
def token_hash(token:str)->str:return hashlib.sha256(token.encode()).hexdigest()
def permissions_for(db:Session,user_id,tenant_id):
 roles=db.scalars(select(RolePermission.permission_code).join(UserRole,(UserRole.tenant_id==RolePermission.tenant_id)&(UserRole.role_id==RolePermission.role_id)).where(UserRole.tenant_id==tenant_id,UserRole.user_id==user_id)).all()
 return set(roles)
def set_auth_cookies(response:Response,session_token:str,csrf_token:str,secure:bool):
 max_age=SESSION_HOURS*3600
 response.set_cookie(SESSION_COOKIE,session_token,max_age=max_age,httponly=True,secure=secure,samesite="strict",path="/")
 response.set_cookie(CSRF_COOKIE,csrf_token,max_age=max_age,httponly=False,secure=secure,samesite="strict",path="/")
def revoke_session(db:Session,raw_token:str|None):
 if raw_token:
  session=db.scalar(select(UserSession).where(UserSession.token_hash==token_hash(raw_token),UserSession.revoked_at.is_(None)))
  if session:session.revoked_at=datetime.now(timezone.utc);db.commit()


def get_current_user(request:Request,db:Session=Depends(get_db),workflow_session:str|None=Cookie(default=None,alias=SESSION_COOKIE)):
 if not workflow_session:raise HTTPException(401,"Authentication required")
 session=db.scalar(select(UserSession).where(UserSession.token_hash==token_hash(workflow_session),UserSession.revoked_at.is_(None),UserSession.expires_at>datetime.now(timezone.utc)))
 if not session:raise HTTPException(401,"Session expired")
 user=db.scalar(select(User).where(User.id==session.user_id,User.tenant_id==session.tenant_id,User.is_active.is_(True)))
 if not user:raise HTTPException(401,"Account inactive")
 employee=db.scalar(select(Employee.id).where(Employee.tenant_id==user.tenant_id,Employee.user_id==user.id,Employee.is_active.is_(True),Employee.archived_at.is_(None)))
 linked=db.scalar(select(Employee.id).where(Employee.tenant_id==user.tenant_id,Employee.user_id==user.id))
 if linked and not employee:raise HTTPException(401,"Employee account inactive")
 db.info["tenant_id"]=user.tenant_id;db.info["actor_id"]=user.id;db.info["session"]=session
 return user

def require_permission(permission:str):
 def check(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
  granted=permissions_for(db,user.id,user.tenant_id)
  if permission not in granted:raise HTTPException(403,"Permission denied")
  return user
 return check

def csrf_protect(request:Request,user:User=Depends(get_current_user),db:Session=Depends(get_db),workflow_csrf:str|None=Cookie(default=None,alias=CSRF_COOKIE)):
 supplied=request.headers.get("X-CSRF-Token")
 session=db.info["session"]
 if request.method not in {"GET","HEAD","OPTIONS"} and (not workflow_csrf or not supplied or not hmac.compare_digest(workflow_csrf,supplied) or not hmac.compare_digest(token_hash(supplied),session.csrf_hash)):raise HTTPException(403,"CSRF validation failed")
 return user

def audit(db,kind,entity_id,action,before=None,after=None):
 from app.models import AuditEvent
 tenant=db.info.get("tenant_id");actor=db.info.get("actor_id")
 if tenant and actor:db.add(AuditEvent(tenant_id=tenant,actor_id=actor,entity_type=kind,entity_id=entity_id,action=action,before_data=before,after_data=after))

def seed_tenant_access(db:Session,tenant_id,admin_user_id):
 from app.models import Permission
 for code,description in PERMISSIONS.items():db.merge(Permission(code=code,description=description))
 db.flush()
 for code,name in ROLE_NAMES.items():
  role=db.scalar(select(Role).where(Role.tenant_id==tenant_id,Role.code==code))
  if not role:role=Role(tenant_id=tenant_id,code=code,name=name,is_system=True);db.add(role);db.flush()
  for permission in ROLE_PERMISSIONS[code]:db.merge(RolePermission(tenant_id=tenant_id,role_id=role.id,permission_code=permission))
 admin=db.scalar(select(Role).where(Role.tenant_id==tenant_id,Role.code=="administrator"))
 db.merge(UserRole(tenant_id=tenant_id,user_id=admin_user_id,role_id=admin.id))


def require_any_permission(*permissions):
 def check(user:User=Depends(get_current_user),db:Session=Depends(get_db)):
  granted=permissions_for(db,user.id,user.tenant_id)
  if not granted.intersection(permissions):raise HTTPException(403,"Permission denied")
  return user
 return check


