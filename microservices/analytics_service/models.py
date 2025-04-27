# microservices/analytics_service/models.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid


class ActivityEvent(BaseModel):
    """Activity event model for tracking student activities"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: int
    event_type: str
    resource_type: str
    resource_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    duration_seconds: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActivityReport(BaseModel):
    """Activity report model for storing generated reports"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str
    created_by: int
    parameters: Dict[str, Any]
    status: str = "processing"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None


class CourseActivity(BaseModel):
    """Course activity summary"""
    course_id: int
    date: str
    event_count: int
    active_students: int
    total_duration_seconds: int


class StudentActivity(BaseModel):
    """Student activity summary"""
    student_id: int
    date: str
    event_count: int
    page_views: int
    resource_views: int
    submissions: int
    total_duration_seconds: int


class EngagementScore(BaseModel):
    """Student engagement score"""
    student_id: int
    course_id: int
    engagement_score: float
    rank: Optional[int] = None
    date: str


class AssignmentAnalytics(BaseModel):
    """Assignment analytics"""
    assignment_id: int
    view_count: int
    submission_count: int
    completion_rate: float
    average_score: Optional[float] = None
    average_time_spent: Optional[float] = None


class StudentProgress(BaseModel):
    """Student progress tracking"""
    student_id: int
    course_id: int
    modules_completed: int
    total_modules: int
    completion_percentage: float
    last_activity_date: Optional[datetime] = None
    estimated_completion_date: Optional[datetime] = None


class CourseCohortAnalytics(BaseModel):
    """Course cohort analytics"""
    course_id: int
    cohort_id: str
    start_date: datetime
    student_count: int
    completion_rate: float
    average_score: float
    dropout_rate: float


class LearningPathAnalytics(BaseModel):
    """Learning path analytics"""
    path_id: int
    path_name: str
    student_count: int
    average_completion_time_days: float
    most_challenging_course_id: Optional[int] = None
    most_dropped_course_id: Optional[int] = None