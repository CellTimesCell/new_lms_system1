# Grading CRUD operations
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from core.lms_core.assignments.models import Submission, Grade, Assignment
from core.lms_core.users.models import User
from core.lms_core.grading import schemas


def get_submission_detail(db: Session, submission_id: int):
    """
    Get detailed view of a submission for grading
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return None

    # Get assignment
    assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()

    # Get student
    student = db.query(User).filter(User.id == submission.student_id).first()

    # Get existing grade
    grade = db.query(Grade).filter(Grade.submission_id == submission_id).order_by(Grade.graded_at.desc()).first()

    # Build response
    result = {
        "id": submission.id,
        "assignment_id": submission.assignment_id,
        "assignment_title": assignment.title if assignment else None,
        "student_id": submission.student_id,
        "student_name": f"{student.first_name} {student.last_name}" if student else None,
        "submitted_at": submission.submitted_at,
        "submission_text": submission.submission_text,
        "submission_files": submission.submission_files,
        "is_late": submission.is_late,
        "status": submission.status,
        "grade": None
    }

    # Add grade if exists
    if grade:
        result["grade"] = {
            "id": grade.id,
            "score": grade.score,
            "feedback": grade.feedback,
            "rubric_scores": grade.rubric_scores,
            "graded_at": grade.graded_at,
            "grader_id": grade.grader_id
        }

    return result


def get_assignment_submissions(db: Session, assignment_id: int):
    """
    Get all submissions for an assignment
    """
    submissions = db.query(Submission).filter(Submission.assignment_id == assignment_id).all()

    result = []
    for submission in submissions:
        # Get student info
        student = db.query(User).filter(User.id == submission.student_id).first()

        # Get latest grade if exists
        grade = db.query(Grade).filter(Grade.submission_id == submission.id).order_by(Grade.graded_at.desc()).first()

        # Build submission overview
        submission_data = {
            "id": submission.id,
            "student_id": submission.student_id,
            "student_name": f"{student.first_name} {student.last_name}" if student else None,
            "submitted_at": submission.submitted_at,
            "is_late": submission.is_late,
            "status": submission.status,
            "score": grade.score if grade else None,
            "graded_at": grade.graded_at if grade else None
        }

        result.append(submission_data)

    return result


def create_or_update_grade(db: Session, submission_id: int, grader_id: int, grade_data: schemas.GradeCreate):
    """
    Create or update a grade for a submission
    """
    # Check if submission exists
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        return None

    # Create new grade
    db_grade = Grade(
        submission_id=submission_id,
        grader_id=grader_id,
        score=grade_data.score,
        feedback=grade_data.feedback,
        rubric_scores=grade_data.rubric_scores,
        graded_at=datetime.utcnow()
    )

    db.add(db_grade)

    # Update submission status
    submission.status = "graded"

    db.commit()
    db.refresh(db_grade)

    return db_grade