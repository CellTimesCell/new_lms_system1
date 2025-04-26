# scripts/create_sample_data.py
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database and models
from sqlalchemy.orm import Session
from infrastructure.databases.database_config import SessionLocal, engine, Base
from core.lms_core.users.models import User, Role, UserProfile
from core.lms_core.courses.models import Course, Module, ContentItem, Enrollment
from core.lms_core.auth.auth import get_password_hash


def create_sample_data():
    """Create sample data for development"""
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(User).count() > 0:
            print("Sample data already exists. Skipping.")
            return

        print("Creating sample data...")

        # Create roles
        admin_role = Role(name="admin", description="Administrator with full system access")
        instructor_role = Role(name="instructor", description="Teacher role with course management permissions")
        student_role = Role(name="student", description="Student role with learning permissions")

        db.add_all([admin_role, instructor_role, student_role])
        db.commit()

        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("adminpass"),
            is_active=True,
            is_verified=True
        )
        admin.roles.append(admin_role)

        # Create instructor
        instructor = User(
            username="teacher",
            email="teacher@example.com",
            first_name="John",
            last_name="Smith",
            hashed_password=get_password_hash("teacherpass"),
            is_active=True,
            is_verified=True
        )
        instructor.roles.append(instructor_role)

        # Create profile for instructor
        instructor_profile = UserProfile(
            bio="Experienced math teacher with 10+ years of teaching",
            timezone="America/New_York"
        )
        instructor.profile = instructor_profile

        # Create students
        students = []
        for i in range(1, 5):
            student = User(
                username=f"student{i}",
                email=f"student{i}@example.com",
                first_name=f"Student{i}",
                last_name="User",
                hashed_password=get_password_hash("studentpass"),
                is_active=True,
                is_verified=True
            )
            student.roles.append(student_role)
            students.append(student)

        db.add_all([admin, instructor] + students)
        db.commit()

        # Create courses
        math_course = Course(
            title="Algebra 101",
            code="MATH101",
            description="Introduction to algebra and mathematical concepts",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=90),
            is_active=True,
            is_published=True,
            instructor_id=instructor.id
        )

        science_course = Course(
            title="Biology Basics",
            code="BIO101",
            description="Introduction to biological concepts and principles",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=90),
            is_active=True,
            is_published=False,  # Not published yet
            instructor_id=instructor.id
        )

        db.add_all([math_course, science_course])
        db.commit()

        # Create modules for math course
        module1 = Module(
            title="Introduction to Algebra",
            description="Basic algebra concepts",
            position=1,
            is_published=True
        )
        module1.courses.append(math_course)

        module2 = Module(
            title="Linear Equations",
            description="Solving linear equations and inequalities",
            position=2,
            is_published=True
        )
        module2.courses.append(math_course)

        db.add_all([module1, module2])
        db.commit()

        # Create content items
        content_items = [
            ContentItem(
                module_id=module1.id,
                title="What is Algebra?",
                content_type="text",
                content="Algebra is a branch of mathematics dealing with symbols and the rules for manipulating these symbols.",
                position=1,
                is_published=True
            ),
            ContentItem(
                module_id=module1.id,
                title="Introduction Video",
                content_type="video",
                content="https://example.com/algebra-intro.mp4",
                position=2,
                is_published=True
            ),
            ContentItem(
                module_id=module2.id,
                title="Solving Linear Equations",
                content_type="text",
                content="A linear equation is an equation that describes a straight line.",
                position=1,
                is_published=True
            )
        ]

        db.add_all(content_items)
        db.commit()

        # Enroll students in courses
        for student in students:
            enrollment = Enrollment(
                student_id=student.id,
                course_id=math_course.id,
                enrollment_date=datetime.now() - timedelta(days=5),
                is_active=True,
                completion_status="in_progress"
            )
            db.add(enrollment)

        db.commit()

        print("Sample data created successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error creating sample data: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()