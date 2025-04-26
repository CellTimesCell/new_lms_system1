# core/lms_core/courses/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# Module schemas
class ModuleBase(BaseModel):
    title: str
    description: Optional[str] = None
    position: int
    is_published: bool = False


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    position: Optional[int] = None
    is_published: Optional[bool] = None


class Module(ModuleBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Content item schemas
class ContentItemBase(BaseModel):
    title: str
    content_type: str
    content: Optional[str] = None
    position: int
    is_published: bool = False


class ContentItemCreate(ContentItemBase):
    module_id: int


class ContentItemUpdate(BaseModel):
    title: Optional[str] = None
    content_type: Optional[str] = None
    content: Optional[str] = None
    position: Optional[int] = None
    is_published: Optional[bool] = None


class ContentItem(ContentItemBase):
    id: int
    module_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# Course schemas
class CourseBase(BaseModel):
    title: str
    code: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    is_published: bool = False


class CourseCreate(CourseBase):
    instructor_id: int


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    instructor_id: Optional[int] = None


class Course(CourseBase):
    id: int
    instructor_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CourseWithModules(Course):
    modules: List[Module] = []

    class Config:
        orm_mode = True


# Enrollment schemas
class EnrollmentBase(BaseModel):
    student_id: int
    course_id: int
    is_active: bool = True


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(BaseModel):
    is_active: Optional[bool] = None
    completion_status: Optional[str] = None


class Enrollment(EnrollmentBase):
    id: int
    enrollment_date: datetime
    completion_status: str
    last_accessed: Optional[datetime] = None

    class Config:
        orm_mode = True