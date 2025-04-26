# core/lms_core/users/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from infrastructure.databases.database_config import Base

# User roles association table
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)


class User(Base):
    """User model for students, teachers, and administrators"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    preferred_language = Column(String, default="en")  # Default to English, can be 'es' for Spanish

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    courses_teaching = relationship("Course", back_populates="instructor")
    courses_enrolled = relationship("Enrollment", back_populates="student")

    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"


class Role(Base):
    """Role model for user permissions"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role")


class UserProfile(Base):
    """Extended user profile information"""
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    bio = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    timezone = Column(String, default="UTC")

    # Relationships
    user = relationship("User", back_populates="profile")


class RolePermission(Base):
    """Permissions for roles"""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission = Column(String, index=True)

    # Relationships
    role = relationship("Role", back_populates="permissions")