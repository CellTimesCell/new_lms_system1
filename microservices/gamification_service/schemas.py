# microservices/gamification_service/schemas.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class BadgeAward(BaseModel):
    """Badge award request schema"""
    user_id: int
    badge_id: int
    awarded_by: Optional[int] = None
    reason: Optional[str] = None


class Badge(BaseModel):
    """Badge details schema"""
    id: int
    name: str
    description: str
    image_url: str
    category: str
    awarded_at: Optional[datetime] = None
    reason: Optional[str] = None

    class Config:
        orm_mode = True


class AchievementProgress(BaseModel):
    """Achievement progress update schema"""
    user_id: int
    achievement_id: int
    progress_value: float
    max_value: float
    metadata: Optional[Dict[str, Any]] = None


class Achievement(BaseModel):
    """Achievement details schema"""
    id: int
    name: str
    description: str
    image_url: str
    progress_value: float
    max_value: float
    completed: bool
    completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ProgressUpdate(BaseModel):
    """Course/module progress update schema"""
    user_id: int
    resource_type: str  # "course" or "module"
    resource_id: int
    progress_percentage: float
    completed: bool = False


class Progress(BaseModel):
    """Course/module progress schema"""
    user_id: int
    resource_type: str
    resource_id: int
    progress_percentage: float
    completed: bool
    last_updated: datetime

    class Config:
        orm_mode = True


class LeaderboardEntry(BaseModel):
    """Leaderboard entry schema"""
    user_id: int
    username: str
    points: int
    position: int


class Leaderboard(BaseModel):
    """Leaderboard schema"""
    course_id: Optional[int] = None
    period: str  # "week", "month", "all-time"
    entries: List[LeaderboardEntry]


class PointsTransaction(BaseModel):
    """Points transaction schema"""
    user_id: int
    course_id: Optional[int] = None
    points: int
    transaction_type: str  # "awarded", "redeemed"
    description: str
    metadata: Optional[Dict[str, Any]] = None


class UserGamificationProfile(BaseModel):
    """User gamification profile schema"""
    user_id: int
    total_points: int
    badges: List[Badge]
    achievements: List[Achievement]
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[datetime] = None