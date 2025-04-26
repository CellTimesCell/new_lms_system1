# tests/conftest.py
import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import models and database configuration
from infrastructure.databases.database_config import Base
from core.lms_core.users.models import User, Role
from security.authentication.auth import get_password_hash

# Create test database
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def db_session():
    # Create in-memory SQLite database for tests
    engine = create_engine(
        TEST_SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Setup test data
    setup_test_data(db)

    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


def setup_test_data(db):
    # Create test roles
    admin_role = Role(name="admin", description="Administrator")
    instructor_role = Role(name="instructor", description="Teacher")
    student_role = Role(name="student", description="Student")

    db.add_all([admin_role, instructor_role, student_role])
    db.commit()

    # Create test users
    admin_user = User(
        username="admin_test",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpass"),
        is_active=True,
        is_verified=True
    )
    admin_user.roles.append(admin_role)

    instructor_user = User(
        username="teacher_test",
        email="teacher@example.com",
        first_name="Teacher",
        last_name="User",
        hashed_password=get_password_hash("teacherpass"),
        is_active=True,
        is_verified=True
    )
    instructor_user.roles.append(instructor_role)

    student_user = User(
        username="student_test",
        email="student@example.com",
        first_name="Student",
        last_name="User",
        hashed_password=get_password_hash("studentpass"),
        is_active=True,
        is_verified=True
    )
    student_user.roles.append(student_role)

    db.add_all([admin_user, instructor_user, student_user])
    db.commit()