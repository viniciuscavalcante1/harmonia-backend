# app/schemas.py
from enum import Enum

from pydantic import BaseModel, EmailStr
from datetime import date
from typing import List, Optional


class HabitBase(BaseModel):
    name: str
    icon: str
    date: date
    is_completed: bool


class HabitCreate(BaseModel):
    name: str
    icon: str


class HabitDefinitionCreate(BaseModel):
    name: str
    icon: str


class HabitDefinition(HabitDefinitionCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class HabitStatus(HabitDefinition):
    is_completed: bool


class HabitHistory(BaseModel):
    current_streak: int
    completed_dates: List[date]


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
    habits: List[HabitStatus] = []


class ChatMessage(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    current_message: str
    history: List[ChatMessage] = []
    user_id: int


class UserUpdate(BaseModel):
    main_goal: str


class SuggestionRequest(BaseModel):
    objective: str


class HabitSuggestion(BaseModel):
    name: str
    icon: str


class Mood(str, Enum):
    feliz = "feliz"
    bem = "bem"
    neutro = "neutro"
    mal = "mal"
    triste = "triste"


class JournalEntryCreate(BaseModel):
    mood: Mood
    content: Optional[str] = None
    date: date


class JournalEntry(BaseModel):
    id: int
    user_id: int
    date: date
    mood: Mood
    content: Optional[str] = None

    class Config:
        from_attributes = True
