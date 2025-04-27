# tests/test_files.py
import requests
import json
import time
import os
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for API
BASE_URL = os.getenv("API_URL", "http://localhost/api/v1")
FILES_API_URL = os.getenv("FILES_API_URL", "http://localhost/api/files")

# Test data
TEST_USER = {
    "username": "instructor_test",
    "email": "instructor@example.com",
    "password": "Secur3P@ssword!"
}

# Global variables to store tokens and IDs
access_token = None
course_id = None  # You might need to set this to an existing course ID
file_id = None


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


def create_test_file():
    # Create a temporary text file for testing
    temp_file = tempfile.NamedTemporaryFile(suffix=".txt", delete=False)
    content = f"This is a test file created at {time.time()}\n"
    content += "Used for testing the file upload API\n"
    content += "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

    temp_file.write(content.encode("utf-8"))
    temp_file.close()

    return temp_file.name


def test_upload_file():
    global file_id

    print("\n--- Testing File Upload ---")

    if not access_token:
        print("No access token, skipping test")
        return False

    # Create a test file
    test_file_path = create_test_file()
    try:
        # Prepare file upload
        files = {
            'file': (os.path.basename(test_file_path), open(test_file_path, 'rb'), 'text/plain')
        }

        data = {
            'description': 'Test file upload',
            'course_id': course_id if course_id else None,
            'is_public': 'true'
        }

        # Upload file
        response = requests.post(
            f"{FILES_API_URL}/upload",
            files=files,
            data=data,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )

        print(f"Upload File Response: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            file_id = data["id"]
            print(f"File uploaded with ID: {file_id}")
            print(data)
            print("File upload test passed!")
            return True
        else:
            print(response.json() if response.text else response.text)
            print("File upload test failed!")
            return False

    finally:
        # Clean up the test file
        os.unlink(test_file_path)


def test_list_files():
    print("\n--- Testing List Files ---")

    if not access_token:
        print("No access token, skipping test")
        return False

    # List files
    params = {}
    if course_id:
        params['course_id'] = course_id

    response = requests.get(
        f"{FILES_API_URL}",
        params=params,
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"List Files Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} files")
        if data:
            print(f"First file: {data[0]['original_filename']}")
        print("List files test passed!")
        return True
    else:
        print(response.json() if response.text else response.text)
        print("List files test failed!")
        return False


def test_download_file():
    print("\n--- Testing File Download ---")

    if not access_token or not file_id:
        print("No access token or file ID, skipping test")
        return False

    # Download file
    response = requests.get(
        f"{FILES_API_URL}/download/{file_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Download File Response: {response.status_code}")

    if response.status_code == 200:
        print(f"File downloaded, content length: {len(response.content)} bytes")
        print("File download test passed!")
        return True
    else:
        print(response.json() if response.text else response.text)
        print("File download test failed!")
        return False


def test_delete_file():
    print("\n--- Testing File Deletion ---")

    if not access_token or not file_id:
        print("No access token or file ID, skipping test")
        return False

    # Delete file
    response = requests.delete(
        f"{FILES_API_URL}/{file_id}",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Delete File Response: {response.status_code}")

    if response.status_code in [200, 204]:
        print("File deletion test passed!")
        return True
    else:
        print(response.json() if response.text else response.text)
        print("File deletion test failed!")
        return False


def run_all_tests():
    print("=== Starting File Management Tests ===")

    # Set an existing course ID
    global course_id
    course_id = 1  # Replace with an actual course ID from your system

    # Login first
    if not login():
        print("Login failed, aborting tests")
        return

    tests = [
        test_upload_file,
        test_list_files,
        test_download_file,
        test_delete_file
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))

    print("\n=== File Management Test Results ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    run_all_tests()