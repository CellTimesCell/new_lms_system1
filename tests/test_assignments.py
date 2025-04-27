# tests/test_assignments.py
import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for API
BASE_URL = os.getenv("API_URL", "http://localhost/api/v1")

# Test data
INSTRUCTOR = {
    "username": "instructor_test",
    "email": "instructor@example.com",
    "password": "Secur3P@ssword!"
}

STUDENT = {
    "username": "student_test",
    "email": "student@example.com",
    "password": "Secur3P@ssword!"
}

# Global variables to store tokens and IDs
instructor_token = None
student_token = None
course_id = None  # You might need to set this to an existing course ID
assignment_id = None
submission_id = None


def login_instructor():
    global instructor_token

    print("\n--- Logging in as Instructor ---")

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": INSTRUCTOR["username"],
            "password": INSTRUCTOR["password"]
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if response.status_code == 200:
        data = response.json()
        instructor_token = data["access_token"]
        print(f"Instructor login successful, token: {instructor_token[:10]}...")
        return True
    else:
        print(f"Instructor login failed: {response.status_code}")
        print(response.json())
        return False


def login_student():
    global student_token

    print("\n--- Logging in as Student ---")

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": STUDENT["username"],
            "password": STUDENT["password"]
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if response.status_code == 200:
        data = response.json()
        student_token = data["access_token"]
        print(f"Student login successful, token: {student_token[:10]}...")
        return True
    else:
        print(f"Student login failed: {response.status_code}")
        print(response.json())
        return False


def test_create_assignment():
    global assignment_id

    print("\n--- Testing Assignment Creation ---")

    if not instructor_token or not course_id:
        print("No instructor token or course ID, skipping test")
        return False

    # Create an assignment
    assignment_data = {
        "title": f"Test Assignment {int(time.time())}",
        "description": "This is a test assignment created by the testing script",
        "course_id": course_id,
        "due_date": "2023-12-15T23:59:59Z",
        "points_possible": 100,
        "submission_type": "online_text",
        "is_published": True
    }

    response = requests.post(
        f"{BASE_URL}/assignments/",
        json=assignment_data,
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Create Assignment Response: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        assignment_id = data["id"]
        print(f"Assignment created with ID: {assignment_id}")
        print(data)
        print("Assignment creation test passed!")
        return True
    else:
        print(response.json())
        print("Assignment creation test failed!")
        return False


def test_get_assignments():
    print("\n--- Testing Get Assignments ---")

    if not instructor_token or not course_id:
        print("No instructor token or course ID, skipping test")
        return False

    # Get all assignments for a course
    response = requests.get(
        f"{BASE_URL}/assignments/course/{course_id}",
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Get Assignments Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} assignments")
        print("Get assignments test passed!")
        return True
    else:
        print(response.json())
        print("Get assignments test failed!")
        return False


def test_get_assignment_details():
    print("\n--- Testing Get Assignment Details ---")

    if not instructor_token or not assignment_id:
        print("No instructor token or assignment ID, skipping test")
        return False

    # Get assignment details
    response = requests.get(
        f"{BASE_URL}/assignments/{assignment_id}",
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Get Assignment Details Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Assignment details: {data['title']}")
        print("Get assignment details test passed!")
        return True
    else:
        print(response.json())
        print("Get assignment details test failed!")
        return False


def test_submit_assignment():
    global submission_id

    print("\n--- Testing Assignment Submission ---")

    if not student_token or not assignment_id:
        print("No student token or assignment ID, skipping test")
        return False

    # Submit assignment
    submission_data = {
        "submission_text": f"This is a test submission created at {time.time()}",
        "submission_files": []
    }

    response = requests.post(
        f"{BASE_URL}/assignments/{assignment_id}/submit",
        json=submission_data,
        headers={
            "Authorization": f"Bearer {student_token}"
        }
    )

    print(f"Submit Assignment Response: {response.status_code}")

    if response.status_code in [200, 201]:
        data = response.json()
        submission_id = data["id"]
        print(f"Submission created with ID: {submission_id}")
        print(data)
        print("Assignment submission test passed!")
        return True
    else:
        print(response.json())
        print("Assignment submission test failed!")
        return False


def test_get_submissions():
    print("\n--- Testing Get Submissions ---")

    if not instructor_token or not assignment_id:
        print("No instructor token or assignment ID, skipping test")
        return False

    # Get all submissions for an assignment
    response = requests.get(
        f"{BASE_URL}/assignments/{assignment_id}/submissions",
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Get Submissions Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} submissions")
        print("Get submissions test passed!")
        return True
    else:
        print(response.json())
        print("Get submissions test failed!")
        return False


def test_get_submission_details():
    print("\n--- Testing Get Submission Details ---")

    if not instructor_token or not submission_id:
        print("No instructor token or submission ID, skipping test")
        return False

    # Get submission details
    response = requests.get(
        f"{BASE_URL}/grading/submissions/{submission_id}",
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Get Submission Details Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Submission details for assignment: {data['assignment_id']}")
        print("Get submission details test passed!")
        return True
    else:
        print(response.json())
        print("Get submission details test failed!")
        return False


def test_grade_submission():
    print("\n--- Testing Submission Grading ---")

    if not instructor_token or not submission_id:
        print("No instructor token or submission ID, skipping test")
        return False

    # Grade submission
    grade_data = {
        "score": 85,
        "feedback": f"Good work! Graded at {time.time()}"
    }

    response = requests.post(
        f"{BASE_URL}/grading/submissions/{submission_id}/grade",
        json=grade_data,
        headers={
            "Authorization": f"Bearer {instructor_token}"
        }
    )

    print(f"Grade Submission Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Grade created with score: {data['score']}")
        print(data)
        print("Grade submission test passed!")
        return True
    else:
        print(response.json())
        print("Grade submission test failed!")
        return False


def test_student_view_submission():
    print("\n--- Testing Student View Submission ---")

    if not student_token or not submission_id:
        print("No student token or submission ID, skipping test")
        return False

    # Student views their submission
    response = requests.get(
        f"{BASE_URL}/assignments/submission/{submission_id}",
        headers={
            "Authorization": f"Bearer {student_token}"
        }
    )

    print(f"Student View Submission Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Submission viewed, status: {data['status']}")

        # Check if graded
        if data['status'] == 'graded' and 'grade' in data:
            print(f"Grade: {data['grade']['score']}")
            print(f"Feedback: {data['grade']['feedback']}")

        print("Student view submission test passed!")
        return True
    else:
        print(response.json())
        print("Student view submission test failed!")
        return False


def run_all_tests():
    print("=== Starting Assignments and Grading Tests ===")

    # Set an existing course ID
    global course_id
    course_id = 1  # Replace with an actual course ID from your system

    # Login first
    if not login_instructor():
        print("Instructor login failed, aborting tests")
        return

    if not login_student():
        print("Student login failed, some tests may fail")

    tests = [
        test_create_assignment,
        test_get_assignments,
        test_get_assignment_details,
        test_submit_assignment,
        test_get_submissions,
        test_get_submission_details,
        test_grade_submission,
        test_student_view_submission
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))

    print("\n=== Assignments and Grading Test Results ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    run_all_tests()