# core/lms_core/assignments/schemas.py
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime


class AssignmentBase(BaseModel):
    """Base assignment schema"""
    title: str
    description: Optional[str] = None
    course_id: int
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    points_possible: float = 100.0
    submission_type: str  # online_text, online_upload, online_quiz, etc.
    is_published: bool = False
    allow_late_submissions: bool = True
    late_submission_penalty: float = 0.0
    rubric_id: Optional[int] = None


class AssignmentCreate(AssignmentBase):
    """Schema for creating an assignment"""
    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment"""
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    available_from: Optional[datetime] = None
    available_until: Optional[datetime] = None
    points_possible: Optional[float] = None
    submission_type: Optional[str] = None
    is_published: Optional[bool] = None
    allow_late_submissions: Optional[bool] = None
    late_submission_penalty: Optional[float] = None
    rubric_id: Optional[int] = None


class Assignment(AssignmentBase):
    """Schema for assignment response"""
    id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class AssignmentDetail(Assignment):
    """Schema for detailed assignment view"""
    submission_count: Optional[int] = None
    graded_count: Optional[int] = None
    average_score: Optional[float] = None
    has_submitted: Optional[bool] = None  # Whether current user has submitted

    class Config:
        orm_mode = True


class SubmissionBase(BaseModel):
    """Base submission schema"""
    submission_text: Optional[str] = None
    submission_files: Optional[List[Dict[str, Any]]] = None


class SubmissionCreate(SubmissionBase):
    """Schema for creating a submission"""
    pass


class Submission(SubmissionBase):
    """Schema for submission response"""
    id: int
    assignment_id: int
    student_id: int
    submitted_at: datetime
    is_late: bool
    status: str  # draft, submitted, graded

    class Config:
        orm_mode = True


class SubmissionOverview(BaseModel):
    """Schema for submission overview"""
    id: int
    assignment_id: int
    student_id: int
    student_name: Optional[str] = None
    submitted_at: datetime
    is_late: bool
    status: str
    score: Optional[float] = None

    class Config:
        orm_mode = True


class SubmissionDetail(Submission):
    """Schema for detailed submission view"""
    student_name: Optional[str] = None
    assignment_title: Optional[str] = None
    grade: Optional[Dict[str, Any]] = None

    class Config:
        orm_mode = True


class GradeBase(BaseModel):
    """Base grade schema"""
    score: float
    feedback: Optional[str] = None
    rubric_scores: Optional[Dict[str, float]] = None


class GradeCreate(GradeBase):
    """Schema for creating a grade"""
    pass


class Grade(GradeBase):
    """Schema for grade response"""
    id: int
    submission_id: int
    grader_id: int
    graded_at: datetime

    class Config:
        orm_mode = True