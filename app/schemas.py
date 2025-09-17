# app/schemas.py
from enum import Enum

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime
from typing import List, Optional

from app.models import ActivityTypeEnum, SleepQualityEnum


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
    user_name: str
    activity: ActivityData
    sleep: SleepData
    daily_insight: str
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


class ActivityBase(BaseModel):
    activity_type: ActivityTypeEnum
    duration: float
    distance: float | None = None
    date: datetime


class ActivityCreate(ActivityBase):
    owner_id: int


class Activity(ActivityBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class FoodItemBase(BaseModel):
    food_name: str
    calories: float
    protein: float
    carbs: float
    fat: float


class FoodItemCreate(FoodItemBase):
    pass


class FoodItem(FoodItemBase):
    id: int
    nutrition_log_id: int

    class Config:
        orm_mode = True


class NutritionLogBase(BaseModel):
    user_id: int
    log_date: datetime
    total_calories: float
    total_protein: float
    total_carbs: float
    total_fat: float
    insights: str | None = None


class NutritionLogCreate(NutritionLogBase):
    items: List[FoodItemCreate]


class NutritionLog(NutritionLogBase):
    id: int
    created_at: datetime
    items: List[FoodItem] = []

    class Config:
        orm_mode = True


class NutritionAnalysisResponse(BaseModel):
    foods: List[FoodItemBase]
    insights: str
    total_calories: float


class WaterLogBase(BaseModel):
    amount_ml: int


class WaterLogCreate(WaterLogBase):
    pass


class WaterLog(WaterLogBase):
    id: int
    user_id: int
    log_date: datetime

    model_config = ConfigDict(from_attributes=True)


class SleepLogBase(BaseModel):
    start_time: datetime
    end_time: datetime
    quality: Optional[SleepQualityEnum] = None


class SleepLogCreate(SleepLogBase):
    pass


class SleepLog(SleepLogBase):
    id: int
    user_id: int
    duration_minutes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeightLogBase(BaseModel):
    weight_kg: float


class WeightLogCreate(WeightLogBase):
    pass


class WeightLog(WeightLogBase):
    id: int
    user_id: int
    log_date: datetime

    model_config = ConfigDict(from_attributes=True)
