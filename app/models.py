from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Date, Boolean, Float, func, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class UserTest(Base):
    __tablename__ = "test_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)


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

    # activities = relationship("PhysicalActivity", back_populates="user")
    # sleep_records = relationship("SleepRecord", back_populates="user")


class Habit(Base):
    __tablename__ = "habits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    icon = Column(String, index=True)
    date = Column(Date, index=True)
    is_completed = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="habits")


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


class CoachQuestion(BaseModel):
    text: str
