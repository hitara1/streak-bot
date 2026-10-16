"""Database models for Habit Streak Bot"""
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Text, Float, Enum, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import enum
import os
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class DifficultyTier(enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class HabitCategory(enum.Enum):
    HEALTH = "health"
    LEARNING = "learning"
    SOCIAL = "social"
    CREATIVE = "creative"
    DISCIPLINE = "discipline"
    CAREER = "career"
    OTHER = "other"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    title = Column(String(50), default="Novice")
    avatar_stage = Column(Integer, default=1)
    timezone = Column(String(50), default="UTC")
    reminder_time = Column(String(10), default="08:00")
    summary_time = Column(String(10), default="21:00")
    is_premium = Column(Boolean, default=False)
    streak_freezes = Column(Integer, default=2)

    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    checkins = relationship("CheckIn", back_populates="user")
    achievements = relationship("UserAchievement", back_populates="user")

    def xp_to_next_level(self):
        return int(100 * (self.level ** 1.5))

    def add_xp(self, amount):
        self.total_xp += amount
        next_level_xp = self.xp_to_next_level()
        leveled_up = False
        while self.total_xp >= next_level_xp:
            self.total_xp -= next_level_xp
            self.level += 1
            leveled_up = True
            next_level_xp = self.xp_to_next_level()
            self.update_title()
            self.update_avatar()
        return leveled_up

    def update_title(self):
        titles = {
            1: "Novice", 5: "Apprentice", 10: "Warrior", 
            20: "Knight", 30: "Champion", 50: "Legend", 
            75: "Mythic", 100: "Immortal"
        }
        for level, title in sorted(titles.items(), reverse=True):
            if self.level >= level:
                self.title = title
                break

    def update_avatar(self):
        stages = {1: 1, 5: 2, 10: 3, 20: 4, 30: 5, 50: 6}
        for level, stage in sorted(stages.items(), reverse=True):
            if self.level >= level:
                self.avatar_stage = stage
                break

class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(Enum(HabitCategory), default=HabitCategory.OTHER)
    difficulty = Column(Enum(DifficultyTier), default=DifficultyTier.MEDIUM)
    frequency = Column(String(20), default="daily")
    times_per_week = Column(Integer, default=7)
    deadline_time = Column(String(10), default="23:59")
    grace_period_minutes = Column(Integer, default=120)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    total_checkins = Column(Integer, default=0)
    rest_days_used_this_week = Column(Integer, default=0)
    week_start_date = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="habits")
    checkins = relationship("CheckIn", back_populates="habit", cascade="all, delete-orphan")

    def xp_reward(self):
        return {"easy": 5, "medium": 10, "hard": 20}[self.difficulty.value]

    def should_check_in_today(self, date=None):
        if date is None:
            date = datetime.utcnow().date()

        if self.frequency == "daily":
            return True
        elif self.frequency == "weekdays":
            return date.weekday() < 5
        elif self.frequency == "weekend":
            return date.weekday() >= 5
        elif self.frequency == "custom":
            week_start = self.week_start_date.date()
            if (date - week_start).days >= 7:
                self.rest_days_used_this_week = 0
                self.week_start_date = datetime.utcnow()
            return self.rest_days_used_this_week < self.times_per_week
        return True

    def is_streak_at_risk(self):
        if not self.should_check_in_today():
            return False
        today = datetime.utcnow().date()
        last_checkin = None
        if self.checkins:
            last_checkin = max(self.checkins, key=lambda x: x.checked_at)
        if not last_checkin:
            return True
        return last_checkin.checked_at.date() < today

class CheckIn(Base):
    __tablename__ = 'checkins'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=False)
    checked_at = Column(DateTime, default=datetime.utcnow)
    xp_earned = Column(Integer, default=0)
    streak_at_checkin = Column(Integer, default=0)
    note = Column(Text)

    user = relationship("User", back_populates="checkins")
    habit = relationship("Habit", back_populates="checkins")

class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon = Column(String(50), default="Trophy")
    condition_type = Column(String(50))
    condition_value = Column(Integer)
    xp_reward = Column(Integer, default=50)

class UserAchievement(Base):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")
    achievement = relationship("Achievement")

class ReminderLog(Base):
    __tablename__ = 'reminder_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    habit_id = Column(Integer, ForeignKey('habits.id'), nullable=True)
    reminder_type = Column(String(50))
    sent_at = Column(DateTime, default=datetime.utcnow)
    was_acknowledged = Column(Boolean, default=False)


def get_database_url():
    """Get database URL from the environment (None if unset)."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        logger.info("DATABASE_URL found in environment")
        return db_url

    logger.info("No DATABASE_URL set, using local SQLite file")
    return None


def init_db(database_url=None):
    if database_url is None:
        database_url = get_database_url()

    if database_url:
        # Normalise Heroku/Railway/Render style URLs
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        try:
            if database_url.startswith("sqlite"):
                engine = create_engine(
                    database_url, connect_args={"check_same_thread": False}
                )
            else:
                # Render's internal URL needs no SSL; external URLs do.
                if database_url.startswith("postgresql://") and "sslmode" not in database_url \
                        and ".render.com" in database_url:
                    sep = "&" if "?" in database_url else "?"
                    database_url += sep + "sslmode=require"
                engine = create_engine(
                    database_url,
                    connect_args={"connect_timeout": 10},
                    pool_pre_ping=True,
                )
            with engine.connect():
                pass
            Base.metadata.create_all(engine)
            logger.info("Database connected (%s)", engine.dialect.name)
            return sessionmaker(bind=engine)
        except Exception as e:
            logger.error("Database connection failed: %s", e)

    # Fallback: local SQLite file (persists only if the filesystem does)
    logger.warning("Using local SQLite file - data is lost if the filesystem is ephemeral")
    engine = create_engine(
        "sqlite:///habit_streak.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def seed_achievements(session):
    """Seed default achievements"""
    achievements = [
        Achievement(name="First Step", description="Check in for the first time", 
                   icon="Footprints", condition_type="total_checkins", condition_value=1, xp_reward=10),
        Achievement(name="7-Day Warrior", description="Maintain a 7-day streak on any habit", 
                   icon="Fire", condition_type="streak", condition_value=7, xp_reward=50),
        Achievement(name="30-Day Champion", description="Maintain a 30-day streak on any habit", 
                   icon="Crown", condition_type="streak", condition_value=30, xp_reward=200),
        Achievement(name="Centurion", description="100 total check-ins across all habits", 
                   icon="Hundred", condition_type="total_checkins", condition_value=100, xp_reward=100),
        Achievement(name="Comeback Kid", description="Restart a habit after breaking a streak", 
                   icon="Recycle", condition_type="streak", condition_value=1),
        Achievement(name="Jack of All Trades", description="Have 5 active habits at once", 
                   icon="Masks", condition_type="habit_count", condition_value=5, xp_reward=75),
        Achievement(name="Early Bird", description="Check in before 7am", 
                   icon="Bird", condition_type="early_checkin", condition_value=1, xp_reward=25),
        Achievement(name="Night Owl", description="Check in after 10pm", 
                   icon="Owl", condition_type="late_checkin", condition_value=1, xp_reward=25),
        Achievement(name="Health Nut", description="50 check-ins in Health category", 
                   icon="Muscle", condition_type="category_checkins", condition_value=50, xp_reward=100),
        Achievement(name="Scholar", description="50 check-ins in Learning category", 
                   icon="Books", condition_type="category_checkins", condition_value=50, xp_reward=100),
        Achievement(name="Social Butterfly", description="50 check-ins in Social category", 
                   icon="Butterfly", condition_type="category_checkins", condition_value=50, xp_reward=100),
        Achievement(name="Level 5", description="Reach level 5", 
                   icon="Star", condition_type="level", condition_value=5, xp_reward=50),
        Achievement(name="Level 20", description="Reach level 20", 
                   icon="Star2", condition_type="level", condition_value=20, xp_reward=200),
        Achievement(name="Level 50", description="Reach level 50", 
                   icon="Sparkles", condition_type="level", condition_value=50, xp_reward=500),
    ]

    for ach in achievements:
        existing = session.query(Achievement).filter_by(name=ach.name).first()
        if not existing:
            session.add(ach)
    session.commit()
