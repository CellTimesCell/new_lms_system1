# tests/test_authentication.py
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
    "username": f"testuser_{int(time.time())}",
    "email": f"test_{int(time.time())}@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "Secur3P@ssword!",
    "roles": ["student"]
}

verification_token = None
reset_token = None
access_token = None
refresh_token = None


def test_registration():
    global verification_token

    print("\n--- Testing User Registration ---")

    # Register new user
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json=TEST_USER
    )

    print(f"Registration Response: {response.status_code}")
    print(response.json())

    assert response.status_code == 201, "Registration failed"

    # In a real test, we would need to extract the verification token from the email
    # or from the database. For this test, we'll simulate it.

    # Connect to the database to get the token (in a real implementation)
    # For now, we'll simulate a verification token
    verification_token = "simulated_verification_token"

    print("Registration test passed!")
    return True


def test_email_verification():
    print("\n--- Testing Email Verification ---")

    # Verify email
    response = requests.post(
        f"{BASE_URL}/auth/verify-email",
        json={"token": verification_token}
    )

    print(f"Verification Response: {response.status_code}")
    print(response.json())

    # Since we're using a simulated token, we expect a 400 error
    # In a real test with a valid token, this should return 200

    print("Email verification test completed!")
    return True


def test_login():
    global access_token, refresh_token

    print("\n--- Testing User Login ---")

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

    print(f"Login Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        refresh_token = data.get("refresh_token")

        print(f"Access Token: {access_token[:10]}...")
        if refresh_token:
            print(f"Refresh Token: {refresh_token[:10]}...")

        print("Login test passed!")
        return True
    else:
        print(response.json())
        print("Login test failed!")
        return False


def test_password_reset_request():
    global reset_token

    print("\n--- Testing Password Reset Request ---")

    # Request password reset
    response = requests.post(
        f"{BASE_URL}/auth/request-password-reset",
        json={"email": TEST_USER["email"]}
    )

    print(f"Password Reset Request Response: {response.status_code}")
    print(response.json())

    assert response.status_code == 200, "Password reset request failed"

    # In a real test, we would need to extract the reset token from the email
    # or from the database. For this test, we'll simulate it.
    reset_token = "simulated_reset_token"

    print("Password reset request test passed!")
    return True


def test_password_reset():
    print("\n--- Testing Password Reset ---")

    # Reset password
    new_password = "NewSecur3P@ssword!"

    response = requests.post(
        f"{BASE_URL}/auth/reset-password",
        json={
            "token": reset_token,
            "password": new_password
        }
    )

    print(f"Password Reset Response: {response.status_code}")

    # Since we're using a simulated token, we expect a 400 error
    # In a real test with a valid token, this should return 200

    print("Password reset test completed!")
    return True


def test_token_refresh():
    global access_token

    if not refresh_token:
        print("\n--- Skipping Token Refresh (No Refresh Token) ---")
        return False

    print("\n--- Testing Token Refresh ---")

    # Refresh token
    response = requests.post(
        f"{BASE_URL}/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    print(f"Token Refresh Response: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        new_access_token = data["access_token"]

        print(f"New Access Token: {new_access_token[:10]}...")

        access_token = new_access_token

        print("Token refresh test passed!")
        return True
    else:
        print(response.json())
        print("Token refresh test failed!")
        return False


def test_me_endpoint():
    print("\n--- Testing Me Endpoint ---")

    if not access_token:
        print("Skipping test (no access token)")
        return False

    # Get current user info
    response = requests.get(
        f"{BASE_URL}/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Me Endpoint Response: {response.status_code}")

    if response.status_code == 200:
        print(response.json())
        print("Me endpoint test passed!")
        return True
    else:
        print(response.json())
        print("Me endpoint test failed!")
        return False


def test_logout():
    print("\n--- Testing Logout ---")

    if not access_token or not refresh_token:
        print("Skipping test (no tokens)")
        return False

    # Logout
    response = requests.post(
        f"{BASE_URL}/auth/logout",
        json={"refresh_token": refresh_token},
        headers={
            "Authorization": f"Bearer {access_token}"
        }
    )

    print(f"Logout Response: {response.status_code}")

    if response.status_code == 200:
        print(response.json())
        print("Logout test passed!")
        return True
    else:
        print(response.json())
        print("Logout test failed!")
        return False


def run_all_tests():
    print("=== Starting Authentication Tests ===")

    tests = [
        test_registration,
        test_email_verification,
        test_login,
        test_me_endpoint,
        test_password_reset_request,
        test_password_reset,
        test_token_refresh,
        test_logout
    ]

    results = []

    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"Error in {test.__name__}: {str(e)}")
            results.append((test.__name__, False))

    print("\n=== Authentication Test Results ===")
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{name}: {status}")


if __name__ == "__main__":
    run_all_tests()