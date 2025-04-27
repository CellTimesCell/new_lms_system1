# microservices/analytics_service/schemas.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
from enum import Enum


class ReportType(str, Enum):
    """Types of analytics reports"""
    STUDENT_ACTIVITY = "student_activity"
    COURSE_ENGAGEMENT = "course_engagement"
    ASSIGNMENT_COMPLETION = "assignment_completion"
    COURSE_COMPARISON = "course_comparison"
    STUDENT_PROGRESS = "student_progress"


class ActivityEventCreate(BaseModel):
    """Schema for creating activity events"""
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


class ActivityEvent(ActivityEventCreate):
    """Schema for activity event responses"""

    class Config:
        orm_mode = True


class ReportRequest(BaseModel):
    """Schema for report generation request"""
    report_type: ReportType
    created_by: int
    parameters: Dict[str, Any]


class ReportResponse(BaseModel):
    """Schema for report generation response"""
    report_id: str
    report_type: ReportType
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        orm_mode = True


class CourseActivityStats(BaseModel):
    """Schema for course activity statistics"""
    date: str
    event_count: int
    active_students: int
    total_duration_hours: float


class StudentActivityRecord(BaseModel):
    """Schema for student activity records"""
    event_type: str
    resource_type: str
    resource_id: Optional[str]
    timestamp: datetime
    duration_seconds: int
    metadata: Dict[str, Any]


class EngagementScore(BaseModel):
    """Schema for student engagement scores"""
    student_id: int
    course_id: int
    date: str
    engagement_score: float


class DashboardStats(BaseModel):
    """Schema for instructor dashboard statistics"""
    course_id: int
    total_students: int
    active_students_last_week: int
    average_engagement_score: float
    total_activity_count: int
    average_session_duration_minutes: float