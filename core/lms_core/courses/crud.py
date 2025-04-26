# core/lms_core/courses/crud.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from core.lms_core.courses.models import Course, Module, ContentItem, Enrollment
from core.lms_core.courses.schemas import (
    CourseCreate, CourseUpdate,
    ModuleCreate, ModuleUpdate,
    ContentItemCreate, ContentItemUpdate,
    EnrollmentCreate, EnrollmentUpdate
)


# Course CRUD operations
def get_course(db: Session, course_id: int) -> Optional[Course]:
    """Get course by ID"""
    return db.query(Course).filter(Course.id == course_id).first()


def get_course_by_code(db: Session, code: str) -> Optional[Course]:
    """Get course by code"""
    return db.query(Course).filter(Course.code == code).first()


def get_courses(
        db: Session, skip: int = 0, limit: int = 100,
        active_only: bool = False, published_only: bool = False
) -> List[Course]:
    """Get all courses with filtering options"""
    query = db.query(Course)

    if active_only:
        query = query.filter(Course.is_active == True)

    if published_only:
        query = query.filter(Course.is_published == True)

    return query.offset(skip).limit(limit).all()


def get_instructor_courses(db: Session, instructor_id: int) -> List[Course]:
    """Get courses taught by an instructor"""
    return db.query(Course).filter(Course.instructor_id == instructor_id).all()


def create_course(db: Session, course: CourseCreate) -> Course:
    """Create a new course"""
    # Check if course code already exists
    if get_course_by_code(db, course.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )

    # Create course
    db_course = Course(**course.dict())

    db.add(db_course)
    db.commit()
    db.refresh(db_course)

    return db_course


def update_course(db: Session, course_id: int, course: CourseUpdate) -> Course:
    """Update course details"""
    db_course = get_course(db, course_id)
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Check code uniqueness if updating
    if course.code and course.code != db_course.code:
        existing_course = get_course_by_code(db, course.code)
        if existing_course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course code already exists"
            )

    # Update fields if provided
    for key, value in course.dict(exclude_unset=True).items():
        setattr(db_course, key, value)

    db.commit()
    db.refresh(db_course)

    return db_course


def delete_course(db: Session, course_id: int) -> bool:
    """Delete a course"""
    db_course = get_course(db, course_id)
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    db.delete(db_course)
    db.commit()

    return True


# Module CRUD operations
def get_module(db: Session, module_id: int) -> Optional[Module]:
    """Get module by ID"""
    return db.query(Module).filter(Module.id == module_id).first()


def get_course_modules(
        db: Session, course_id: int,
        published_only: bool = False
) -> List[Module]:
    """Get all modules for a course"""
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    query = db.query(Module).join(Module.courses).filter(Course.id == course_id)

    if published_only:
        query = query.filter(Module.is_published == True)

    return query.order_by(Module.position).all()


def create_module(db: Session, module: ModuleCreate, course_id: int) -> Module:
    """Create a new module and add to course"""
    # Check if course exists
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )

    # Create module
    db_module = Module(**module.dict())

    # Add to course
    db_module.courses.append(course)

    db.add(db_module)
    db.commit()
    db.refresh(db_module)

    return db_module


def update_module(db: Session, module_id: int, module: ModuleUpdate) -> Module:
    """Update module details"""
    db_module = get_module(db, module_id)
    if not db_module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # Update fields if provided
    for key, value in module.dict(exclude_unset=True).items():
        setattr(db_module, key, value)

    db.commit()
    db.refresh(db_module)

    return db_module


def delete_module(db: Session, module_id: int) -> bool:
    """Delete a module"""
    db_module = get_module(db, module_id)
    if not db_module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    db.delete(db_module)
    db.commit()

    return True


# Content Item CRUD operations
def get_content_item(db: Session, item_id: int) -> Optional[ContentItem]:
    """Get content item by ID"""
    return db.query(ContentItem).filter(ContentItem.id == item_id).first()


def get_module_content_items(
        db: Session, module_id: int,
        published_only: bool = False
) -> List[ContentItem]:
    """Get all content items for a module"""
    module = get_module(db, module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    query = db.query(ContentItem).filter(ContentItem.module_id == module_id)

    if published_only:
        query = query.filter(ContentItem.is_published == True)

    return query.order_by(ContentItem.position).all()


def create_content_item(db: Session, item: ContentItemCreate) -> ContentItem:
    """Create a new content item"""
    # Check if module exists
    module = get_module(db, item.module_id)
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )

    # Create content item
    db_item = ContentItem(**item.dict())

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


def update_content_item(db: Session, item_id: int, item: ContentItemUpdate) -> ContentItem:
    """Update content item details"""
    db_item = get_content_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content item not found"
        )

    # Update fields if provided
    for key, value in item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)

    return db_item


def delete_content_item(db: Session, item_id: int) -> bool:
    """Delete a content item"""
    db_item = get_content_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content item not found"
        )

    db.delete(db_item)
    db.commit()

    return True


# Enrollment CRUD operations
def get_enrollment(db: Session, enrollment_id: int) -> Optional[Enrollment]:
    """Get enrollment by ID"""
    return db.query(Enrollment).filter(Enrollment.id == enrollment_id).first()


def get_student_enrollment(db: Session, student_id: int, course_id: int) -> Optional[Enrollment]:
    """Get enrollment for a specific student and course"""
    return db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id
    ).first()


def get_course_enrollments(db: Session, course_id: int, active_only: bool = False) -> List[Enrollment]:
    """Get all enrollments for a course"""
    query = db.query(Enrollment).filter(Enrollment.course_id == course_id)

    if active_only:
        query = query.filter(Enrollment.is_active == True)

    return query.all()


def get_student_enrollments(db: Session, student_id: int, active_only: bool = False) -> List[Enrollment]:
    """Get all enrollments for a student"""
    query = db.query(Enrollment).filter(Enrollment.student_id == student_id)

    if active_only:
        query = query.filter(Enrollment.is_active == True)

    return query.all()


def create_enrollment(db: Session, enrollment: EnrollmentCreate) -> Enrollment:
    """Enroll a student in a course"""
    # Check if enrollment already exists
    existing_enrollment = get_student_enrollment(db, enrollment.student_id, enrollment.course_id)
    if existing_enrollment:
        if existing_enrollment.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student already enrolled in this course"
            )
        else:
            # Reactivate enrollment
            existing_enrollment.is_active = True
            existing_enrollment.enrollment_date = datetime.utcnow()
            db.commit()
            db.refresh(existing_enrollment)
            return existing_enrollment

    # Create enrollment
    db_enrollment = Enrollment(
        student_id=enrollment.student_id,
        course_id=enrollment.course_id,
        is_active=enrollment.is_active,
        enrollment_date=datetime.utcnow(),
        completion_status="not_started"
    )

    db.add(db_enrollment)
    db.commit()
    db.refresh(db_enrollment)

    return db_enrollment


def update_enrollment(db: Session, enrollment_id: int, enrollment: EnrollmentUpdate) -> Enrollment:
    """Update enrollment details"""
    db_enrollment = get_enrollment(db, enrollment_id)
    if not db_enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    # Update fields if provided
    for key, value in enrollment.dict(exclude_unset=True).items():
        setattr(db_enrollment, key, value)

    db.commit()
    db.refresh(db_enrollment)

    return db_enrollment


def delete_enrollment(db: Session, enrollment_id: int) -> bool:
    """Delete an enrollment"""
    db_enrollment = get_enrollment(db, enrollment_id)
    if not db_enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )

    db.delete(db_enrollment)
    db.commit()

    return True