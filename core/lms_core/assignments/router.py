# core/lms_core/assignments/router.py - Add submission endpoint
@router.post("/{assignment_id}/submit", response_model=schemas.Submission)
async def submit_assignment(
        assignment_id: int,
        submission: schemas.SubmissionCreate,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Submit an assignment"""
    # Verify the assignment exists
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Verify user is enrolled in the course
    enrollment = crud.get_student_enrollment(db, current_user.id, assignment.course_id)
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this course"
        )

    # Create submission with current user as student
    submission_data = submission.dict()
    submission_data["student_id"] = current_user.id
    submission_data["assignment_id"] = assignment_id

    # Check if past due date
    if assignment.due_date and datetime.utcnow() > assignment.due_date:
        submission_data["is_late"] = True

    return crud.create_submission(db, submission_data)