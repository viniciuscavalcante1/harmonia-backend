from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Date, Boolean
from .database import Base

class UserTest(Base):
    __tablename__ = "test_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class CoachQuestion(BaseModel):
    text: str