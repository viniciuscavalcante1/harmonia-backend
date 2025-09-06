# app/schemas.py
from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List


class HabitBase(BaseModel):
    name: str
    icon: str
    date: date
    is_completed: bool


class HabitCreate(BaseModel):
    name: str
    icon: str


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
    habits: List[Habit] = []

    class Config:
        from_attributes = True


class ActivityData(BaseModel):
    steps: int


class SleepData(BaseModel):
    duration: str


class DashboardDataResponse(BaseModel):
    userName: str
    activity: ActivityData
    sleep: SleepData
    dailyInsight: str
    habits: List[Habit] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    current_message: str
    history: List[ChatMessage] = []
    user_id: int
