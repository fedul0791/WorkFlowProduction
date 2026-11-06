from sqlalchemy import Column, Integer, String, JSON
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    nfc_chip_id = Column(String, unique=True)
    name = Column(String)
    role = Column(String)
    manual_data = Column(JSON)