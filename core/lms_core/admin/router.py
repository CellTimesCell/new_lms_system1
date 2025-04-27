# core/lms_core/admin/router.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from infrastructure.databases.database_config import get_db
from core.lms_core.auth.auth import get_current_active_user, has_role
from core.lms_core.users.models import User, Role
from core.lms_core.users.schemas import User as UserSchema, Role as RoleSchema
from core.lms_core.courses.models import Course
from core.lms_core.assignments.models import Assignment, Submission

router = APIRouter()


@router.get("/dashboard", response_model=Dict)
async def admin_dashboard(
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Get admin dashboard overview statistics"""
    # Get basic counts
    user_count = db.query(User).count()
    course_count = db.query(Course).count()
    assignment_count = db.query(Assignment).count()
    submission_count = db.query(Submission).count()

    # Get active users (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(User).filter(User.updated_at >= thirty_days_ago).count()

    # Get role distribution
    role_distribution = []
    roles = db.query(Role).all()

    for role in roles:
        count = db.query(User).join(User.roles).filter(Role.id == role.id).count()
        role_distribution.append({
            "role": role.name,
            "count": count
        })

    # Get recent activities
    recent_submissions = db.query(Submission).order_by(Submission.submitted_at.desc()).limit(5).all()
    recent_submissions_data = [
        {
            "id": submission.id,
            "student_id": submission.student_id,
            "assignment_id": submission.assignment_id,
            "submitted_at": submission.submitted_at
        }
        for submission in recent_submissions
    ]

    return {
        "statistics": {
            "users": user_count,
            "courses": course_count,
            "assignments": assignment_count,
            "submissions": submission_count,
            "active_users_30d": active_users
        },
        "role_distribution": role_distribution,
        "recent_activities": {
            "submissions": recent_submissions_data
        }
    }


@router.get("/users", response_model=Dict)
async def admin_users_list(
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        active_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Get users with filtering and pagination"""
    # Base query
    query = db.query(User)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.username.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term))
        )

    if role:
        role_obj = db.query(Role).filter(Role.name == role).first()
        if role_obj:
            query = query.join(User.roles).filter(Role.id == role_obj.id)

    if active_only:
        query = query.filter(User.is_active == True)

    # Get total count
    total = query.count()

    # Apply pagination
    users = query.order_by(User.id).offset(skip).limit(limit).all()

    # Format response
    user_list = [UserSchema.from_orm(user) for user in users]

    return {
        "items": user_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/roles", response_model=List[RoleSchema])
async def admin_roles_list(
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Get all roles"""
    roles = db.query(Role).all()
    return [RoleSchema.from_orm(role) for role in roles]


@router.get("/courses", response_model=Dict)
async def admin_courses_list(
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        instructor_id: Optional[int] = None,
        active_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Get courses with filtering and pagination"""
    # Base query
    query = db.query(Course)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Course.title.ilike(search_term)) |
            (Course.code.ilike(search_term)) |
            (Course.description.ilike(search_term))
        )

    if instructor_id:
        query = query.filter(Course.instructor_id == instructor_id)

    if active_only:
        query = query.filter(Course.is_active == True)

    # Get total count
    total = query.count()

    # Apply pagination
    courses = query.order_by(Course.id).offset(skip).limit(limit).all()

    # Format response
    course_list = []
    for course in courses:
        # Get enrollment count
        enrollment_count = db.query(Enrollment).filter(
            Enrollment.course_id == course.id,
            Enrollment.is_active == True
        ).count()

        course_dict = {
            "id": course.id,
            "title": course.title,
            "code": course.code,
            "is_active": course.is_active,
            "is_published": course.is_published,
            "instructor_id": course.instructor_id,
            "instructor_name": f"{course.instructor.first_name} {course.instructor.last_name}" if course.instructor else None,
            "enrollment_count": enrollment_count,
            "start_date": course.start_date,
            "end_date": course.end_date,
            "created_at": course.created_at
        }

        course_list.append(course_dict)

    return {
        "items": course_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/system-settings", status_code=status.HTTP_200_OK)
async def update_system_settings(
        settings: Dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin"]))
):
    """Update system settings"""
    # In a real implementation, this would save to a settings table or configuration
    # For this example, we'll just return success
    return {"message": "Settings updated successfully"}