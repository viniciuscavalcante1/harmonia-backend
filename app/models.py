import datetime
import enum

from pydantic import BaseModel
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Boolean,
    Float,
    func,
    ForeignKey,
    UniqueConstraint,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    email = Column(String(100), unique=True, index=True)

    birth_date = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    initial_weight_kg = Column(Float, nullable=True)

    main_goal = Column(String(50), nullable=True)
    activity_level = Column(String(20), nullable=True)
    signup_date = Column(Date, default=func.now())
    plan_type = Column(String(20), nullable=False, default="Gratuito")
    has_apple_watch = Column(Boolean, default=False)

    habit_definitions = relationship(
        "HabitDefinition", back_populates="owner", cascade="all, delete-orphan"
    )

    activities = relationship("ActivityLog", back_populates="owner")

    # activities = relationship("PhysicalActivity", back_populates="user")
    # sleep_records = relationship("SleepRecord", back_populates="user")


class HabitDefinition(Base):
    __tablename__ = "habit_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    icon = Column(String, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="habit_definitions")
    completions = relationship(
        "HabitCompletion", back_populates="definition", cascade="all, delete-orphan"
    )


class HabitCompletion(Base):
    __tablename__ = "habit_completions"

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habit_definitions.id"))
    date = Column(Date, index=True)

    definition = relationship("HabitDefinition", back_populates="completions")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, index=True, default=datetime.date.today)

    mood = Column(String(50))

    content = Column(String, nullable=True)

    __table_args__ = (UniqueConstraint("user_id", "date", name="_user_date_uc"),)

    owner = relationship("User")


class ActivityTypeEnum(str, enum.Enum):
    running = "Corrida"
    walking = "Caminhada"
    cycling = "Ciclismo"
    strengthTraining = "Treino de Força"


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String, nullable=False)
    duration = Column(Float, nullable=False)
    distance = Column(Float, nullable=True)
    date = Column(DateTime, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="activities")

    def __str__(self):
        return (
            f"activity_type: {self.activity_type}, date: {self.date},"
            f" duration: {self.duration}, distance: {self.distance}"
        )

    def __repr__(self):
        return self.__str__()


class NutritionLog(Base):
    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    log_date = Column(DateTime(timezone=True), nullable=False)
    total_calories = Column(Float, nullable=False)
    total_protein = Column(Float, nullable=False)
    total_carbs = Column(Float, nullable=False)
    total_fat = Column(Float, nullable=False)
    insights = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("FoodItem", back_populates="log", cascade="all, delete-orphan")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    nutrition_log_id = Column(Integer, ForeignKey("nutrition_logs.id"))
    food_name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)

    log = relationship("NutritionLog", back_populates="items")


class WaterLog(Base):
    __tablename__ = "water_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    amount_ml = Column(Integer, nullable=False)
    log_date = Column(DateTime(timezone=True), server_default=func.now())


class CoachQuestion(BaseModel):
    text: str
