# File service schemas
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileCreate(BaseModel):
    """Schema for creating file records"""
    original_filename: str
    file_size: int
    file_type: str
    content_type: str
    course_id: Optional[int] = None
    module_id: Optional[int] = None
    assignment_id: Optional[int] = None
    submission_id: Optional[int] = None
    is_public: bool = False
    description: Optional[str] = None


class FileResponse(BaseModel):
    """Schema for file response"""
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    content_type: str
    created_at: datetime
    url: str

    class Config:
        orm_mode = True