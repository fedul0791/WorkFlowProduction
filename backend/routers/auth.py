from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class RegisterRequest(BaseModel):
    nfc_chip_id: str
    name: str
    role: str

class ManualRegisterRequest(BaseModel):
    name: str
    role: str
    manual_data: dict

@router.post("/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.nfc_chip_id == request.nfc_chip_id).first()
    if existing_user:
        return {"error": "NFC-чип уже зарегистрирован"}
    new_user = User(
        nfc_chip_id=request.nfc_chip_id,
        name=request.name,
        role=request.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id}

@router.post("/register/manual")
def register_user_manual(request: ManualRegisterRequest, db: Session = Depends(get_db)):
    new_user = User(
        name=request.name,
        role=request.role,
        manual_data=request.manual_data
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id}