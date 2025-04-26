# core/lms_core/users/crud.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from core.lms_core.users.models import User, Role, UserProfile
from core.lms_core.users.schemas import UserCreate, UserUpdate, UserProfileCreate, UserProfileUpdate
from core.lms_core.auth.auth import get_password_hash


# User CRUD operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """Create a new user"""
    # Check if username or email already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create user
    db_user = User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
        is_active=user.is_active,
        is_verified=False,
        preferred_language=user.preferred_language
    )

    # Add roles
    for role_name in user.roles:
        role = db.query(Role).filter(Role.name == role_name).first()
        if role:
            db_user.roles.append(role)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def update_user(db: Session, user_id: int, user: UserUpdate) -> User:
    """Update user details"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields if provided
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)

    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user"""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    db.delete(db_user)
    db.commit()

    return True


# Role CRUD operations
def get_role(db: Session, role_id: int) -> Optional[Role]:
    """Get role by ID"""
    return db.query(Role).filter(Role.id == role_id).first()


def get_role_by_name(db: Session, name: str) -> Optional[Role]:
    """Get role by name"""
    return db.query(Role).filter(Role.name == name).first()


def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
    """Get all roles with pagination"""
    return db.query(Role).offset(skip).limit(limit).all()


# User Profile CRUD operations
def get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """Get user profile by user ID"""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def create_user_profile(db: Session, user_id: int, profile: UserProfileCreate) -> UserProfile:
    """Create user profile"""
    # Check if user exists
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if profile already exists
    existing_profile = get_user_profile(db, user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )

    # Create profile
    db_profile = UserProfile(
        user_id=user_id,
        bio=profile.bio,
        profile_picture=profile.profile_picture,
        timezone=profile.timezone
    )

    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)

    return db_profile


def update_user_profile(db: Session, user_id: int, profile: UserProfileUpdate) -> UserProfile:
    """Update user profile"""
    db_profile = get_user_profile(db, user_id)
    if not db_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    # Update fields if provided
    for key, value in profile.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)

    return db_profile