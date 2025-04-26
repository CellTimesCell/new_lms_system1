# Course models for the LMS system
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from infrastructure.databases.database_config import Base
from core.lms_core.users.models import User

# Course-Module association table
course_modules = Table(
    'course_modules',
    Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id')),
    Column('module_id', Integer, ForeignKey('modules.id'))
)


class Course(Base):
    """Course model representing a class or subject"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(Text)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    instructor = relationship("User", back_populates="courses_teaching")
    enrollments = relationship("Enrollment", back_populates="course")
    modules = relationship("Module", secondary=course_modules, back_populates="courses")
    assignments = relationship("Assignment", back_populates="course")


class Module(Base):
    """Module within a course"""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    position = Column(Integer)  # Order within the course
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    courses = relationship("Course", secondary=course_modules, back_populates="modules")
    content_items = relationship("ContentItem", back_populates="module")


class ContentItem(Base):
    """Content item within a module (text, video, etc.)"""
    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("modules.id"))
    title = Column(String, index=True)
    content_type = Column(String)  # text, video, file, etc.
    content = Column(Text)  # For text content or URL to other content
    position = Column(Integer)  # Order within the module
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    module = relationship("Module", back_populates="content_items")


class Enrollment(Base):
    """Student enrollment in a course"""
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrollment_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    completion_status = Column(String, default="not_started")  # not_started, in_progress, completed
    last_accessed = Column(DateTime, nullable=True)

    # Relationships
    student = relationship("User", back_populates="courses_enrolled")
    course = relationship("Course", back_populates="enrollments")