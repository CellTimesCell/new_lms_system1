# Grading router for instructor grading
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from infrastructure.databases.database_config import get_db
from core.lms_core.auth.auth import get_current_active_user, has_role
from core.lms_core.users.models import User
from core.lms_core.assignments.models import Assignment, Submission, Grade
from core.lms_core.grading import schemas, crud

router = APIRouter()


@router.get("/submissions/{submission_id}", response_model=schemas.SubmissionDetail)
async def get_submission_detail(
        submission_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed view of a submission for grading
    """
    # Get submission with related data
    submission = crud.get_submission_detail(db, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Check permissions
    # Instructors can view submissions for their courses
    # Students can only view their own submissions
    user_roles = [role.name for role in current_user.roles]
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()

    if "admin" not in user_roles and "instructor" not in user_roles:
        # Student trying to view submission
        if current_user.id != submission.student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this submission"
            )
    elif "instructor" in user_roles and assignment and assignment.course:
        # Instructor trying to view submission
        if current_user.id != assignment.course.instructor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the instructor for this course"
            )

    return submission


@router.post("/submissions/{submission_id}/grade", response_model=schemas.Grade)
async def grade_submission(
        submission_id: int,
        grade_data: schemas.GradeCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """
    Grade a submission (instructors only)
    """
    # Get submission
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Check if user is instructor for the course
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        # Check if user is instructor for this course
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course or course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the instructor for this course"
            )

    # Create or update grade
    return crud.create_or_update_grade(
        db=db,
        submission_id=submission_id,
        grader_id=current_user.id,
        grade_data=grade_data
    )


@router.get("/assignments/{assignment_id}/submissions", response_model=List[schemas.SubmissionOverview])
async def list_assignment_submissions(
        assignment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(has_role(["admin", "instructor"]))
):
    """
    List all submissions for an assignment (instructors only)
    """
    # Get assignment
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    # Check if user is instructor for the course
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles:
        course = db.query(Course).filter(Course.id == assignment.course_id).first()
        if not course or course.instructor_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the instructor for this course"
            )

    # Get submissions for assignment
    return crud.get_assignment_submissions(db, assignment_id)