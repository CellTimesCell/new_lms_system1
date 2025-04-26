# Assignment models for the LMS system
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime, Table, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from infrastructure.databases.database_config import Base


class Assignment(Base):
    """Assignment model representing a task to be completed"""
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    course_id = Column(Integer, ForeignKey("courses.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime, nullable=True)
    available_from = Column(DateTime, nullable=True)
    available_until = Column(DateTime, nullable=True)
    points_possible = Column(Float, default=100.0)
    submission_type = Column(String)  # online_text, online_upload, online_quiz, etc.
    is_published = Column(Boolean, default=False)
    allow_late_submissions = Column(Boolean, default=True)
    late_submission_penalty = Column(Float, default=0.0)  # percentage
    rubric_id = Column(Integer, ForeignKey("rubrics.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="assignments")
    created_by = relationship("User")
    submissions = relationship("Submission", back_populates="assignment")
    rubric = relationship("Rubric", back_populates="assignments")


class Submission(Base):
    """Student submission for an assignment"""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    submitted_at = Column(DateTime, default=datetime.utcnow)
    submission_text = Column(Text, nullable=True)
    submission_files = Column(JSON, nullable=True)  # JSON array of file URLs
    is_late = Column(Boolean, default=False)
    status = Column(String, default="submitted")  # draft, submitted, graded

    # Relationships
    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User")
    grades = relationship("Grade", back_populates="submission")


class Grade(Base):
    """Grade for a submission"""
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    grader_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float)
    feedback = Column(Text, nullable=True)
    rubric_scores = Column(JSON, nullable=True)  # JSON object of rubric criterion scores
    graded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="grades")
    grader = relationship("User")


class Rubric(Base):
    """Rubric for grading assignments"""
    __tablename__ = "rubrics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    created_by = relationship("User")
    criteria = relationship("RubricCriterion", back_populates="rubric")
    assignments = relationship("Assignment", back_populates="rubric")


class RubricCriterion(Base):
    """Criterion for a rubric"""
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rubric_id = Column(Integer, ForeignKey("rubrics.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    points_possible = Column(Float)
    position = Column(Integer)

    # Relationships
    rubric = relationship("Rubric", back_populates="criteria")
    rating_levels = relationship("RatingLevel", back_populates="criterion")


class RatingLevel(Base):
    """Rating level for a rubric criterion"""
    __tablename__ = "rating_levels"

    id = Column(Integer, primary_key=True, index=True)
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id"))
    title = Column(String)
    description = Column(Text, nullable=True)
    points = Column(Float)
    position = Column(Integer)

    # Relationships
    criterion = relationship("RubricCriterion", back_populates="rating_levels")