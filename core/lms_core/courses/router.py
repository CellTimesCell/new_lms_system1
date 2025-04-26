# core/lms_core/courses/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from infrastructure.databases.database_config import get_db
from core.lms_core.courses import crud, schemas
from core.lms_core.auth.auth import get_current_active_user, has_role
from core.lms_core.users.models import User

router = APIRouter()


# Course routes
@router.post("/", response_model=schemas.Course, status_code=status.HTTP_201_CREATED)
def create_course(
        course: schemas.CourseCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """Create a new course (admin/instructor only)"""
    return crud.create_course(db=db, course=course)


@router.get("/", response_model=List[schemas.Course])
def read_courses(
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        published_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all courses with filtering options"""
    # Regular users can only see published courses
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and "instructor" not in user_roles:
        published_only = True

    return crud.get_courses(
        db=db, skip=skip, limit=limit,
        active_only=active_only, published_only=published_only
    )


@router.get("/taught", response_model=List[schemas.Course])
def read_taught_courses(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get courses taught by current user"""
    user_roles = [role.name for role in current_user.roles]
    if "instructor" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not an instructor"
        )

    return crud.get_instructor_courses(db=db, instructor_id=current_user.id)


@router.get("/{course_id}", response_model=schemas.CourseWithModules)
def read_course(
        course_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get course details with modules"""
    course = crud.get_course(db, course_id=course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check permissions - regular users can only see published courses
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and "instructor" not in user_roles and not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Course not published"
        )

    # Get modules
    published_only = True
    if "admin" in user_roles or "instructor" in user_roles or current_user.id == course.instructor_id:
        published_only = False

    modules = crud.get_course_modules(db, course_id, published_only=published_only)

    # Create response
    course_dict = schemas.Course.from_orm(course).dict()
    return {**course_dict, "modules": modules}


@router.put("/{course_id}", response_model=schemas.Course)
def update_course(
        course_id: int,
        course: schemas.CourseUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Update course details"""
    # Check if course exists
    db_course = crud.get_course(db, course_id)
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check permissions - only admin or the instructor can update
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != db_course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.update_course(db=db, course_id=course_id, course=course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
        course_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Delete a course (admin only)"""
    crud.delete_course(db=db, course_id=course_id)
    return {"ok": True}


# Module routes
@router.post("/{course_id}/modules", response_model=schemas.Module, status_code=status.HTTP_201_CREATED)
def create_module(
        course_id: int,
        module: schemas.ModuleCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Create a new module for a course"""
    # Check permissions - only admin or the instructor can add modules
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.create_module(db=db, module=module, course_id=course_id)


@router.get("/{course_id}/modules", response_model=List[schemas.Module])
def read_modules(
        course_id: int,
        published_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all modules for a course"""
    # Check permissions - regular users can only see published modules
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        published_only = True

    return crud.get_course_modules(db=db, course_id=course_id, published_only=published_only)


# Content item routes
@router.post("/modules/{module_id}/content", response_model=schemas.ContentItem, status_code=status.HTTP_201_CREATED)
def create_content_item(
        module_id: int,
        item: schemas.ContentItemCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Create a new content item for a module"""
    # Check permissions - only admin or the instructor can add content
    module = crud.get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Get course for this module to check instructor
    courses = module.courses
    if not courses:
        raise HTTPException(status_code=404, detail="Module not associated with any course")

    course = courses[0]  # Get first course

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.create_content_item(db=db, item=item)


@router.get("/modules/{module_id}/content", response_model=List[schemas.ContentItem])
def read_content_items(
        module_id: int,
        published_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all content items for a module"""
    # Check permissions - regular users can only see published content
    module = crud.get_module(db, module_id)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    # Get course for this module to check instructor
    courses = module.courses
    if not courses:
        raise HTTPException(status_code=404, detail="Module not associated with any course")

    course = courses[0]  # Get first course

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        published_only = True

    return crud.get_module_content_items(db=db, module_id=module_id, published_only=published_only)


# Enrollment routes
@router.post("/enroll", response_model=schemas.Enrollment, status_code=status.HTTP_201_CREATED)
def create_enrollment(
        enrollment: schemas.EnrollmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Enroll a student in a course"""
    # Check permissions - only admin can enroll others
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != enrollment.student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    # Check if course is published for regular students
    course = crud.get_course(db, enrollment.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    if "admin" not in user_roles and "instructor" not in user_roles and not course.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enroll in unpublished course"
        )

    return crud.create_enrollment(db=db, enrollment=enrollment)


@router.get("/enrollments/me", response_model=List[schemas.Enrollment])
def read_my_enrollments(
        active_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get current user's enrollments"""
    return crud.get_student_enrollments(db=db, student_id=current_user.id, active_only=active_only)


@router.get("/{course_id}/enrollments", response_model=List[schemas.Enrollment])
def read_course_enrollments(
        course_id: int,
        active_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all enrollments for a course"""
    # Check permissions - only admin or the instructor can see enrollments
    course = crud.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.get_course_enrollments(db=db, course_id=course_id, active_only=active_only)