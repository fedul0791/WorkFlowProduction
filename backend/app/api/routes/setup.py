import re
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password, seed_tenant_access, set_auth_cookies, token_hash
from app.db.session import get_db
from app.models import Company, User, UserSession

router = APIRouter(prefix="/api/v1/setup", tags=["first-run setup"])


class InitialEnterpriseInput(BaseModel):
    company_name: str = Field(min_length=2, max_length=180)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=256)

    @field_validator("company_name")
    @classmethod
    def clean_company_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Company name must contain at least two characters")
        return value

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("A valid email address is required")
        return value


def setup_is_available(db: Session) -> bool:
    return not db.scalar(select(Company.id).limit(1)) and not db.scalar(select(User.id).limit(1))


@router.get("/status")
def setup_status(db: Session = Depends(get_db)):
    return {"setup_required": setup_is_available(db)}


@router.post("", status_code=201)
def create_initial_enterprise(payload: InitialEnterpriseInput, request: Request, response: Response, db: Session = Depends(get_db)):
    origin = request.headers.get("origin")
    allowed_origins = {value.strip() for value in get_settings().cors_origins.split(",") if value.strip()}
    if origin and origin not in allowed_origins:
        raise HTTPException(403, "Untrusted origin")

    # Serialize first-run attempts so only one company and owner account can be created.
    db.execute(text("SELECT pg_advisory_xact_lock(6843219057123)"))
    if not setup_is_available(db):
        raise HTTPException(409, "Initial setup has already been completed")

    tenant_id = uuid4()
    company = Company(id=tenant_id, tenant_id=tenant_id, name=payload.company_name)
    owner = User(tenant_id=tenant_id, email=payload.email, password_hash=hash_password(payload.password))
    db.add(company)
    db.add(owner)
    db.flush()
    seed_tenant_access(db, tenant_id, owner.id)

    now = datetime.now(timezone.utc)
    raw_session = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    session = UserSession(
        tenant_id=tenant_id,
        user_id=owner.id,
        token_hash=token_hash(raw_session),
        csrf_hash=token_hash(csrf_token),
        expires_at=now + timedelta(hours=12),
    )
    db.add(session)
    db.commit()
    set_auth_cookies(response, raw_session, csrf_token, get_settings().app_env.lower() not in {"development", "dev", "test"})
    return {
        "company": {"id": str(company.id), "name": company.name},
        "user": {"id": str(owner.id), "email": owner.email, "tenant_id": str(owner.tenant_id)},
        "expires_at": session.expires_at.isoformat(),
    }
