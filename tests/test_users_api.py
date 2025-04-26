# tests/test_users_api.py
import pytest
from fastapi.testclient import TestClient

from core.lms_core.main import app
from security.authentication.auth import create_access_token

# Setup test client
client = TestClient(app)


def test_get_users(db_session):
    # Create test token for admin
    admin_token_data = {
        "sub": "1",  # admin_user.id
        "username": "admin_test",
        "roles": ["admin"]
    }
    access_token, _ = create_access_token(admin_token_data)

    # Test get users endpoint
    response = client.get(
        "/api/v1/users/",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Assert response
    assert response.status_code == 200
    users = response.json()
    assert len(users) >= 3  # At least our 3 test users

    # Verify user data
    assert any(user["username"] == "admin_test" for user in users)
    assert any(user["username"] == "teacher_test" for user in users)
    assert any(user["username"] == "student_test" for user in users)


def test_create_user(db_session):
    # Create test token for admin
    admin_token_data = {
        "sub": "1",  # admin_user.id
        "username": "admin_test",
        "roles": ["admin"]
    }
    access_token, _ = create_access_token(admin_token_data)

    # Test create user endpoint
    new_user_data = {
        "username": "new_test_user",
        "email": "newuser@example.com",
        "first_name": "New",
        "last_name": "User",
        "password": "newuserpass",
        "roles": ["student"]
    }

    response = client.post(
        "/api/v1/users/",
        json=new_user_data,
        headers={"Authorization": f"Bearer {access_token}"}
    )

    # Assert response
    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == "new_test_user"
    assert created_user["email"] == "newuser@example.com"
    assert "hashed_password" not in created_user