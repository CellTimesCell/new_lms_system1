# Grading schemas
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime


class GradeCreate(BaseModel):
    """Schema for creating a grade"""
    score: float
    feedback: Optional[str] = None
    rubric_scores: Optional[Dict[str, float]] = None


class Grade(BaseModel):
    """Schema for grade response"""
    id: int
    submission_id: int
    grader_id: int
    score: float
    feedback: Optional[str] = None
    rubric_scores: Optional[Dict[str, Any]] = None
    graded_at: datetime

    class Config:
        orm_mode = True


class SubmissionDetail(BaseModel):
    """Schema for detailed submission view"""
    id: int
    assignment_id: int
    assignment_title: Optional[str] = None
    student_id: int
    student_name: Optional[str] = None
    submitted_at: datetime
    submission_text: Optional[str] = None
    submission_files: Optional[List[Dict[str, Any]]] = None
    is_late: bool
    status: str
    grade: Optional[Grade] = None

    class Config:
        orm_mode = True


class SubmissionOverview(BaseModel):
    """Schema for submission overview in list"""
    id: int
    student_id: int
    student_name: Optional[str] = None
    submitted_at: datetime
    is_late: bool
    status: str
    score: Optional[float] = None
    graded_at: Optional[datetime] = None

    class Config:
        orm_mode = True