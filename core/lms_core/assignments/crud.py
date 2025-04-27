# core/lms_core/assignments/crud.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime

from core.lms_core.assignments.models import Assignment, Submission, Grade, Rubric, RubricCriterion, RatingLevel
from core.lms_core.assignments.schemas import (
    AssignmentCreate, AssignmentUpdate,
    SubmissionCreate, GradeCreate,
    RubricCreate, RubricCriterionCreate, RatingLevelCreate
)
from core.lms_core.users.models import User
from core.lms_core.courses.models import Course, Enrollment, Module


def get_assignment(db: Session, assignment_id: int) -> Optional[Assignment]:
    """Get assignment by ID"""
    return db.query(Assignment).filter(Assignment.id == assignment_id).first()


def get_course_assignments(
        db: Session, course_id: int, published_only: bool = False
) -> List[Assignment]:
    """Get all assignments for a course"""
    query = db.query(Assignment).filter(Assignment.course_id == course_id)

    if published_only:
        query = query.filter(Assignment.is_published == True)

    return query.order_by(Assignment.due_date.asc()).all()


def create_assignment(db: Session, assignment: Dict) -> Assignment:
    """Create a new assignment"""
    db_assignment = Assignment(**assignment)

    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)

    return db_assignment


def update_assignment(db: Session, assignment_id: int, assignment: AssignmentUpdate) -> Assignment:
    """Update assignment details"""
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Update fields if provided
    update_data = assignment.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_assignment, key, value)

    db.commit()
    db.refresh(db_assignment)

    return db_assignment


def delete_assignment(db: Session, assignment_id: int) -> bool:
    """Delete an assignment"""
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(db_assignment)
    db.commit()

    return True


def get_assignment_with_details(db: Session, assignment_id: int, student_id: Optional[int] = None) -> Dict:
    """Get assignment with detailed information"""
    # Get assignment
    assignment = get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Get submission statistics
    submission_count = db.query(Submission).filter(Submission.assignment_id == assignment_id).count()

    # Get graded count
    graded_count = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.status == "graded"
    ).count()

    # Get average score
    avg_score_query = db.query(
        func.avg(Grade.score).label('avg_score')
    ).join(
        Submission, Grade.submission_id == Submission.id
    ).filter(
        Submission.assignment_id == assignment_id
    ).first()

    avg_score = avg_score_query[0] if avg_score_query[0] else None

    # Check if student has submitted (if student_id provided)
    has_submitted = None
    if student_id:
        submission = db.query(Submission).filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == student_id
        ).first()
        has_submitted = submission is not None

    # Convert assignment to dict
    result = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "course_id": assignment.course_id,
        "created_by_id": assignment.created_by_id,
        "due_date": assignment.due_date,
        "available_from": assignment.available_from,
        "available_until": assignment.available_until,
        "points_possible": assignment.points_possible,
        "submission_type": assignment.submission_type,
        "is_published": assignment.is_published,
        "allow_late_submissions": assignment.allow_late_submissions,
        "late_submission_penalty": assignment.late_submission_penalty,
        "rubric_id": assignment.rubric_id,
        "created_at": assignment.created_at,
        "updated_at": assignment.updated_at,
        "submission_count": submission_count,
        "graded_count": graded_count,
        "average_score": avg_score,
        "has_submitted": has_submitted
    }

    return result


def is_student_enrolled(db: Session, student_id: int, course_id: int) -> bool:
    """Check if a student is enrolled in a course"""
    enrollment = db.query(Enrollment).filter(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
        Enrollment.is_active == True
    ).first()

    return enrollment is not None


def get_submission(db: Session, submission_id: int) -> Optional[Submission]:
    """Get submission by ID"""
    return db.query(Submission).filter(Submission.id == submission_id).first()


def get_student_submissions(
        db: Session, assignment_id: int, student_id: int
) -> List[Dict]:
    """Get all submissions for a student on an assignment"""
    submissions = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == student_id
    ).all()

    # Format response with student name
    result = []
    for submission in submissions:
        # Get the latest grade if any
        grade = db.query(Grade).filter(
            Grade.submission_id == submission.id
        ).order_by(Grade.graded_at.desc()).first()

        # Get student name
        student = db.query(User).filter(User.id == student_id).first()
        student_name = f"{student.first_name} {student.last_name}" if student else None

        result.append({
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "student_id": submission.student_id,
            "student_name": student_name,
            "submitted_at": submission.submitted_at,
            "is_late": submission.is_late,
            "status": submission.status,
            "score": grade.score if grade else None
        })

    return result


def get_assignment_submissions(db: Session, assignment_id: int) -> List[Dict]:
    """Get all submissions for an assignment with student names"""
    # Join with User to get student names
    submissions = db.query(
        Submission, User.first_name, User.last_name
    ).join(
        User, Submission.student_id == User.id
    ).filter(
        Submission.assignment_id == assignment_id
    ).all()

    # Format results
    result = []
    for submission, first_name, last_name in submissions:
        # Get the latest grade if any
        grade = db.query(Grade).filter(
            Grade.submission_id == submission.id
        ).order_by(Grade.graded_at.desc()).first()

        result.append({
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "student_id": submission.student_id,
            "student_name": f"{first_name} {last_name}",
            "submitted_at": submission.submitted_at,
            "is_late": submission.is_late,
            "status": submission.status,
            "score": grade.score if grade else None
        })

    return result


def create_submission(db: Session, submission: Dict) -> Submission:
    """Create a new submission"""
    # Check if there's already a submission
    existing = db.query(Submission).filter(
        Submission.assignment_id == submission["assignment_id"],
        Submission.student_id == submission["student_id"]
    ).first()

    if existing:
        # Update existing submission
        for key, value in submission.items():
            setattr(existing, key, value)

        existing.submitted_at = datetime.utcnow()
        existing.status = "submitted"

        db.commit()
        db.refresh(existing)

        return existing

    # Create new submission
    db_submission = Submission(**submission, status="submitted")

    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    return db_submission


def get_submission_detail(db: Session, submission_id: int) -> Dict:
    """Get detailed submission with assignment and student info"""
    # Get submission
    submission = get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get assignment and student info
    assignment = get_assignment(db, submission.assignment_id)
    student = db.query(User).filter(User.id == submission.student_id).first()

    # Get latest grade if any
    grade = db.query(Grade).filter(
        Grade.submission_id == submission.id
    ).order_by(Grade.graded_at.desc()).first()

    # Format result
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


def get_grade(db: Session, grade_id: int) -> Optional[Grade]:
    """Get grade by ID"""
    return db.query(Grade).filter(Grade.id == grade_id).first()


def create_or_update_grade(db: Session, submission_id: int, grader_id: int, grade_data: GradeCreate) -> Grade:
    """Create or update a grade for a submission"""
    # Check if submission exists
    submission = get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Check if there's already a grade
    existing = db.query(Grade).filter(
        Grade.submission_id == submission_id
    ).first()

    if existing:
        # Update existing grade
        existing.score = grade_data.score
        existing.feedback = grade_data.feedback
        existing.rubric_scores = grade_data.rubric_scores
        existing.graded_at = datetime.utcnow()

        db.commit()
        db.refresh(existing)

        # Update submission status
        submission.status = "graded"
        db.commit()

        return existing

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


def get_rubric(db: Session, rubric_id: int) -> Optional[Rubric]:
    """Get rubric by ID"""
    return db.query(Rubric).filter(Rubric.id == rubric_id).first()


def get_instructor_rubrics(db: Session, instructor_id: int) -> List[Rubric]:
    """Get all rubrics created by an instructor"""
    return db.query(Rubric).filter(Rubric.created_by_id == instructor_id).all()


def create_rubric(db: Session, rubric: RubricCreate, created_by_id: int) -> Rubric:
    """Create a new rubric"""
    # Create rubric
    db_rubric = Rubric(
        title=rubric.title,
        created_by_id=created_by_id
    )

    db.add(db_rubric)
    db.commit()
    db.refresh(db_rubric)

    # Create criteria
    for i, criterion in enumerate(rubric.criteria):
        db_criterion = RubricCriterion(
            rubric_id=db_rubric.id,
            title=criterion.title,
            description=criterion.description,
            points_possible=criterion.points_possible,
            position=i + 1
        )

        db.add(db_criterion)
        db.commit()
        db.refresh(db_criterion)

        # Create rating levels
        for j, level in enumerate(criterion.rating_levels):
            db_level = RatingLevel(
                criterion_id=db_criterion.id,
                title=level.title,
                description=level.description,
                points=level.points,
                position=j + 1
            )

            db.add(db_level)

    db.commit()

    return db_rubric


def get_rubric_with_criteria(db: Session, rubric_id: int) -> Dict:
    """Get rubric with all criteria and rating levels"""
    rubric = get_rubric(db, rubric_id)
    if not rubric:
        raise HTTPException(status_code=404, detail="Rubric not found")

    # Get criteria
    criteria = db.query(RubricCriterion).filter(
        RubricCriterion.rubric_id == rubric_id
    ).order_by(RubricCriterion.position).all()

    criteria_list = []
    for criterion in criteria:
        # Get rating levels
        levels = db.query(RatingLevel).filter(
            RatingLevel.criterion_id == criterion.id
        ).order_by(RatingLevel.position).all()

        levels_list = [
            {
                "id": level.id,
                "title": level.title,
                "description": level.description,
                "points": level.points,
                "position": level.position
            }
            for level in levels
        ]

        criteria_list.append({
            "id": criterion.id,
            "title": criterion.title,
            "description": criterion.description,
            "points_possible": criterion.points_possible,
            "position": criterion.position,
            "rating_levels": levels_list
        })

    # Format result
    result = {
        "id": rubric.id,
        "title": rubric.title,
        "created_by_id": rubric.created_by_id,
        "created_at": rubric.created_at,
        "updated_at": rubric.updated_at,
        "criteria": criteria_list
    }

    return result