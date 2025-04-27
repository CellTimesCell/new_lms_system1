# tests/test_assignments_api.py
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from core.lms_core.main import app
from security.authentication.auth import create_access_token

# Setup test client
client = TestClient(app)


def test_create_assignment(db_session):
    # Create test token for instructor
    instructor_token_data = {
        "sub": "2",  # instructor_user.id
        "username": "teacher_test",
        "roles": ["instructor"]
    }
    access_token, _ = create_access_token(instructor_token_data)

    # Test create assignment endpoint
    assignment_data = {
        "title": "Test Assignment",
        "description": "This is a test assignment",
        "course_id": 1,
        "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "points_possible": 100,
        "submission_type": "online_text"
    }

    response = client.post(
        "/api/v1/assignments/",
        json=assignment_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Assert response
    assert response.status_code == 201
    created_assignment = response.json()
    assert created_assignment["title"] == "Test Assignment"
    assert created_assignment["course_id"] == 1
    assert created_assignment["points_possible"] == 100


def test_get_assignments_for_course(db_session):
    # Create test token for student
    student_token_data = {
        "sub": "3",  # student_user.id
        "username": "student_test",
        "roles": ["student"]
    }
    access_token, _ = create_access_token(student_token_data)

    # Test get assignments endpoint
    response = client.get(
        "/api/v1/courses/1/assignments",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Assert response
    assert response.status_code == 200
    assignments = response.json()
    assert isinstance(assignments, list)
    if len(assignments) > 0:
        assert "title" in assignments[0]
        assert "due_date" in assignments[0]


def test_submit_assignment(db_session):
    # Create test token for student
    student_token_data = {
        "sub": "3",  # student_user.id
        "username": "student_test",
        "roles": ["student"]
    }
    access_token, _ = create_access_token(student_token_data)

    # First, get an assignment to submit to
    response = client.get(
        "/api/v1/courses/1/assignments",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assignments = response.json()

    if len(assignments) == 0:
        pytest.skip("No assignments available to test submission")

    assignment_id = assignments[0]["id"]

    # Test submit assignment endpoint
    submission_data = {
        "submission_text": "This is my assignment submission for testing.",
        "submission_files": []
    }

    response = client.post(
        f"/api/v1/assignments/{assignment_id}/submit",
        json=submission_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Assert response
    assert response.status_code == 200  # or 201 depending on your API design
    submission = response.json()
    assert submission["assignment_id"] == assignment_id
    assert submission["submission_text"] == "This is my assignment submission for testing."


def test_get_submission(db_session):
    # Create test token for instructor
    instructor_token_data = {
        "sub": "2",  # instructor_user.id
        "username": "teacher_test",
        "roles": ["instructor"]
    }
    access_token, _ = create_access_token(instructor_token_data)

    # Test get submission endpoint - we assume a submission with ID 1 exists
    response = client.get(
        "/api/v1/grading/submissions/1",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # If the submission doesn't exist, this test might need to create one first
    if response.status_code == 404:
        pytest.skip("Submission ID 1 not found, cannot test get submission")

    # Assert response
    assert response.status_code == 200
    submission = response.json()
    assert "assignment_id" in submission
    assert "student_id" in submission
    assert "submission_text" in submission


def test_grade_submission(db_session):
    # Create test token for instructor
    instructor_token_data = {
        "sub": "2",  # instructor_user.id
        "username": "teacher_test",
        "roles": ["instructor"]
    }
    access_token, _ = create_access_token(instructor_token_data)

    # We assume a submission with ID 1 exists
    submission_id = 1

    # Test grade submission endpoint
    grade_data = {
        "score": 85,
        "feedback": "Good work! Could improve on citation formatting."
    }

    response = client.post(
        f"/api/v1/grading/submissions/{submission_id}/grade",
        json=grade_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # If the submission doesn't exist, this test might need to create one first
    if response.status_code == 404:
        pytest.skip(f"Submission ID {submission_id} not found, cannot test grading")

    # Assert response
    assert response.status_code == 200
    grade = response.json()
    assert grade["submission_id"] == submission_id
    assert grade["score"] == 85
    assert "feedback" in grade