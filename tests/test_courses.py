# tests/test_courses.py
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
TEST_USER = {
    "username": "instructor_test",
    "email": "instructor@example.com",
    "password": "Secur3P@ssword!"
}

# Global variables to store tokens and IDs
access_token = None
course_id = None
module_id = None
content_id = None


def login():
    global access_token

    print("\n--- Logging in ---")

    # Login
    response = requests.post(
        f"{BASE_URL}/auth/token",
        data={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"Login successful, token: {access_token[:10]}...")
        return True
    else:
        print(f"Login failed: {response.status_code}")
        print(response.json())
        return False


def test_create_course():
    global course_id

    print("\n--- Testing Course Creation ---")

    if not access_token:
        print("No access token, skipping test")
        return False

    # Create a course
    course_data = {
        "title": f"Test Course {int(time.time())}",
        "code": f"TEST{int(time.time())}",
        "description": "This is a test course created by the testing script",
        "start_date": "2023-09-01T00:00:00Z",
        "end_date": "2023-12-31T23:59:59Z",
        "is_active": True,
        "is_published": True,
        "instructor_id": 2  # Assuming instructor ID is 2, adjust as needed
    }

    response = requests.post(
        f"{BASE_URL}/courses/",
        json=course_data,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Create Course Response: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        course_id = data["id"]
        print(f"Course created with ID: {course_id}")
        print(data)
        print("Course creation test passed!")
        return True
    else:
        print(response.json())
        print("Course creation test failed!")
        return False


def test_get_courses():
    print("\n--- Testing Get Courses ---")

    if not access_token:
        print("No access token, skipping test")
        return False

    # Get all courses
    response = requests.get(
        f"{BASE_URL}/courses/",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Get Courses Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} courses")
        print("Get courses test passed!")
        return True
    else:
        print(response.json())
        print("Get courses test failed!")
        return False


def test_get_course_details():
    print("\n--- Testing Get Course Details ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Get course details
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Get Course Details Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Course details: {data['title']}")
        print("Get course details test passed!")
        return True
    else:
        print(response.json())
        print("Get course details test failed!")
        return False


def test_create_module():
    global module_id

    print("\n--- Testing Module Creation ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Create a module
    module_data = {
        "title": f"Test Module {int(time.time())}",
        "description": "This is a test module created by the testing script",
        "position": 1,
        "is_published": True
    }

    response = requests.post(
        f"{BASE_URL}/courses/{course_id}/modules",
        json=module_data,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Create Module Response: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        module_id = data["id"]
        print(f"Module created with ID: {module_id}")
        print(data)
        print("Module creation test passed!")
        return True
    else:
        print(response.json())
        print("Module creation test failed!")
        return False


def test_get_modules():
    print("\n--- Testing Get Modules ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Get all modules for a course
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}/modules",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Get Modules Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} modules")
        print("Get modules test passed!")
        return True
    else:
        print(response.json())
        print("Get modules test failed!")
        return False


def test_create_content():
    global content_id

    print("\n--- Testing Content Creation ---")

    if not access_token or not module_id:
        print("No access token or module ID, skipping test")
        return False

    # Create content item
    content_data = {
        "title": f"Test Content {int(time.time())}",
        "content_type": "text",
        "content": "This is a test content item created by the testing script",
        "position": 1,
        "is_published": True,
        "module_id": module_id
    }

    response = requests.post(
        f"{BASE_URL}/courses/modules/{module_id}/content",
        json=content_data,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Create Content Response: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        content_id = data["id"]
        print(f"Content created with ID: {content_id}")
        print(data)
        print("Content creation test passed!")
        return True
    else:
        print(response.json())
        print("Content creation test failed!")
        return False


def test_get_content():
    print("\n--- Testing Get Content ---")

    if not access_token or not module_id:
        print("No access token or module ID, skipping test")
        return False

    # Get all content for a module
    response = requests.get(
        f"{BASE_URL}/courses/modules/{module_id}/content",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Get Content Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} content items")
        print("Get content test passed!")
        return True
    else:
        print(response.json())
        print("Get content test failed!")
        return False


def test_update_course():
    print("\n--- Testing Course Update ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Update course
    update_data = {
        "description": f"Updated description at {time.time()}"
    }

    response = requests.put(
        f"{BASE_URL}/courses/{course_id}",
        json=update_data,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Update Course Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Course updated: {data['description']}")
        print("Course update test passed!")
        return True
    else:
        print(response.json())
        print("Course update test failed!")
        return False


def test_enroll_student():
    print("\n--- Testing Student Enrollment ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Enroll a student
    enrollment_data = {
        "student_id": 3,  # Assuming student ID is 3, adjust as needed
        "course_id": course_id,
        "is_active": True
    }

    response = requests.post(
        f"{BASE_URL}/courses/enroll",
        json=enrollment_data,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Enroll Student Response: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print(f"Enrollment created with ID: {data['id']}")
        print(data)
        print("Student enrollment test passed!")
        return True
    else:
        print(response.json())
        print("Student enrollment test failed!")
        return False


def test_get_enrollments():
    print("\n--- Testing Get Enrollments ---")

    if not access_token or not course_id:
        print("No access token or course ID, skipping test")
        return False

    # Get enrollments for a course
    response = requests.get(
        f"{BASE_URL}/courses/{course_id}/enrollments",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Get Enrollments Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} enrollments")
        print("Get enrollments test passed!")
        return True
    else:
        print(response.json())
        print("Get enrollments test failed!")
        return False


def run_all_tests():
    print("=== Starting Course Management Tests ===")

    # Login first
    if not login():
        print("Login failed, aborting tests")
        return

    tests = [
        test_create_course,
        test_get_courses,
        test_get_course_details,
        test_create_module,
        test_get_modules,
        test_create_content,
        test_get_content,
        test_update_course,
        test_enroll_student,
        test_get_enrollments
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))

    print("\n=== Course Management Test Results ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    run_all_tests()