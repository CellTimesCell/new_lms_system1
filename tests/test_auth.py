# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import our app and models
from core.lms_core.main import app
from infrastructure.databases.database_config import Base, get_db
from core.lms_core.users.models import User, Role
from core.lms_core.auth.auth import get_password_hash

# Setup test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test client
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)

    # Create a test session
    db = TestingSessionLocal()

    # Create test data
    create_test_data(db)

    # Override get_db dependency
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield db

    # Cleanup after test
    Base.metadata.drop_all(bind=engine)


def create_test_data(db):
    # Create test roles
    admin_role = Role(name="admin", description="Administrator")
    instructor_role = Role(name="instructor", description="Teacher")
    student_role = Role(name="student", description="Student")

    db.add_all([admin_role, instructor_role, student_role])
    db.commit()

    # Create test users
    test_admin = User(
        username="test_admin",
        email="test_admin@example.com",
        first_name="Test",
        last_name="Admin",
        hashed_password=get_password_hash("testadminpass"),
        is_active=True,
        is_verified=True
    )
    test_admin.roles.append(admin_role)

    test_instructor = User(
        username="test_instructor",
        email="test_instructor@example.com",
        first_name="Test",
        last_name="Instructor",
        hashed_password=get_password_hash("testinstructorpass"),
        is_active=True,
        is_verified=True
    )
    test_instructor.roles.append(instructor_role)

    test_student = User(
        username="test_student",
        email="test_student@example.com",
        first_name="Test",
        last_name="Student",
        hashed_password=get_password_hash("teststudentpass"),
        is_active=True,
        is_verified=True
    )
    test_student.roles.append(student_role)

    db.add_all([test_admin, test_instructor, test_student])
    db.commit()


def test_login(test_db):
    # Test valid login
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_admin",
            "password": "testadminpass"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["username"] == "test_admin"
    assert "admin" in data["roles"]

    # Test invalid login
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_admin",
            "password": "wrongpassword"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 401


def test_password_reset_request(test_db):
    # Test password reset request
    response = client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "test_admin@example.com"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data