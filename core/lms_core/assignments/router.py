# core/lms_core/assignments/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from infrastructure.databases.database_config import get_db
from core.lms_core.assignments import crud, schemas
from core.lms_core.auth.auth import get_current_active_user, has_role
from core.lms_core.users.models import User
from core.lms_core.courses.crud import get_course

router = APIRouter()


@router.post("/", response_model=schemas.Assignment, status_code=status.HTTP_201_CREATED)
async def create_assignment(
        assignment: schemas.AssignmentCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """Create a new assignment"""
    # Verify the course exists
    course = get_course(db, assignment.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Verify instructor is teaching the course or user is admin
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create assignments for courses you teach"
        )

    # Add current user as creator
    assignment_data = assignment.dict()
    assignment_data["created_by_id"] = current_user.id

    return crud.create_assignment(db=db, assignment=assignment_data)


@router.get("/{assignment_id}", response_model=schemas.AssignmentDetail)
async def get_assignment(
        assignment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get assignment details"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check permissions - only published assignments are visible to students
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and "instructor" not in user_roles:
        if not assignment.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assignment not available"
            )

        # Verify student is enrolled in the course
        if not crud.is_student_enrolled(db, current_user.id, assignment.course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )

    return assignment


@router.put("/{assignment_id}", response_model=schemas.Assignment)
async def update_assignment(
        assignment_id: int,
        assignment: schemas.AssignmentUpdate,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """Update assignment details"""
    db_assignment = crud.get_assignment(db, assignment_id)
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify instructor is teaching the course or user is admin
    user_roles = [role.name for role in current_user.roles]
    course = get_course(db, db_assignment.course_id)

    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update assignments for courses you teach"
        )

    return crud.update_assignment(db=db, assignment_id=assignment_id, assignment=assignment)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
        assignment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """Delete an assignment"""
    db_assignment = crud.get_assignment(db, assignment_id)
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify instructor is teaching the course or user is admin
    user_roles = [role.name for role in current_user.roles]
    course = get_course(db, db_assignment.course_id)

    if "admin" not in user_roles and current_user.id != course.instructor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete assignments for courses you teach"
        )

    crud.delete_assignment(db=db, assignment_id=assignment_id)
    return {"ok": True}


@router.get("/course/{course_id}", response_model=List[schemas.Assignment])
async def get_course_assignments(
        course_id: int,
        published_only: bool = False,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all assignments for a course"""
    # Verify the course exists
    course = get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check permissions
    user_roles = [role.name for role in current_user.roles]

    # Regular students can only see published assignments
    if "admin" not in user_roles and "instructor" not in user_roles:
        published_only = True

        # Verify student is enrolled in the course
        if not crud.is_student_enrolled(db, current_user.id, course_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this course"
            )

    return crud.get_course_assignments(db=db, course_id=course_id, published_only=published_only)


@router.post("/{assignment_id}/submit", response_model=schemas.Submission)
async def submit_assignment(
        assignment_id: int,
        submission: schemas.SubmissionCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Submit an assignment"""
    # Verify the assignment exists
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify the assignment is published
    if not assignment.is_published:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit to an unpublished assignment"
        )

    # Verify user is enrolled in the course
    if not crud.is_student_enrolled(db, current_user.id, assignment.course_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

    # Check if past due date and late submissions are not allowed
    now = datetime.utcnow()
    is_late = assignment.due_date and now > assignment.due_date

    if is_late and not assignment.allow_late_submissions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Late submissions are not allowed for this assignment"
        )

    # Create submission with current user as student
    submission_data = submission.dict()
    submission_data["student_id"] = current_user.id
    submission_data["assignment_id"] = assignment_id
    submission_data["is_late"] = is_late

    return crud.create_submission(db=db, submission=submission_data)


@router.get("/{assignment_id}/submissions", response_model=List[schemas.SubmissionOverview])
async def get_assignment_submissions(
        assignment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get all submissions for an assignment (instructors only)"""
    # Verify the assignment exists
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check permissions - only instructors teaching the course or admins can see all submissions
    user_roles = [role.name for role in current_user.roles]

    if "admin" not in user_roles:
        course = get_course(db, assignment.course_id)
        if current_user.id != course.instructor_id:
            # Students can only see their own submissions
            return crud.get_student_submissions(db, assignment_id, current_user.id)

    return crud.get_assignment_submissions(db, assignment_id)


@router.get("/submission/{submission_id}", response_model=schemas.SubmissionDetail)
async def get_submission(
        submission_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """Get a specific submission"""
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Check permissions - instructors, admins, or the submitting student
    user_roles = [role.name for role in current_user.roles]

    if "admin" not in user_roles and current_user.id != submission.student_id:
        # Check if instructor of the course
        assignment = crud.get_assignment(db, submission.assignment_id)
        course = get_course(db, assignment.course_id)

        if current_user.id != course.instructor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this submission"
            )

    return submission