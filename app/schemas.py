# app/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date


class HabitBase(BaseModel):
    name: str
    icon: str
    date: date
    is_completed: bool


class HabitCreate(HabitBase):
    pass


class Habit(HabitBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    habits: list[Habit] = []

    class Config:
        from_attributes = True
