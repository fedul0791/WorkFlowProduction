from getpass import getpass
import re
from uuid import uuid4
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import Company,User
from app.core.security import hash_password,seed_tenant_access

def main():
 with SessionLocal() as db:
  companies=db.scalars(select(Company).where(Company.archived_at.is_(None)).order_by(Company.name)).all()
  if not companies:
   name=input("Enterprise name: ").strip()
   if not name:raise SystemExit("Enterprise name is required")
   cid=uuid4();company=Company(id=cid,tenant_id=cid,name=name);db.add(company);db.flush()
  elif len(companies)==1:
   company=companies[0]
   print(f"Using existing enterprise: {company.name} ({company.id})")
  else:
   for c in companies:print(f"{c.id}  {c.name}")
   cid=input("Tenant UUID to initialize: ").strip()
   company=next((x for x in companies if str(x.id)==cid),None)
   if not company:raise SystemExit("Unknown enterprise")
  if db.scalar(select(User.id).where(User.tenant_id==company.tenant_id)):raise SystemExit("This enterprise already has an account. Use its Administrator account to create further users.")
  email=input("Administrator email: ").strip().lower()
  if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):raise SystemExit("A valid email is required")
  if db.scalar(select(User.id).where(User.email==email)):raise SystemExit("Email already exists in another enterprise")
  password=getpass("Administrator password (12+ characters): ")
  confirm=getpass("Repeat password: ")
  if password!=confirm:raise SystemExit("Passwords do not match")
  account=User(tenant_id=company.tenant_id,email=email,password_hash=hash_password(password));db.add(account);db.flush();seed_tenant_access(db,company.tenant_id,account.id);db.commit()
  print(f"Administrator created for {company.name} ({company.id}). Sign in at /de/anmelden.")
if __name__=="__main__":main()
