# core/lms_core/users/router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from infrastructure.databases.database_config import get_db
from core.lms_core.users import crud, schemas
from core.lms_core.auth.auth import get_current_active_user, has_role

router = APIRouter()


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(
        user: schemas.UserCreate,
        db: Session = Depends(get_db)
):
    """Create a new user"""
    return crud.create_user(db=db, user=user)


@router.get("/", response_model=List[schemas.User])
def read_users(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(has_role(["admin"]))
):
    """Get all users (admin only)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/me", response_model=schemas.UserWithProfile)
def read_user_me(
        current_user: schemas.User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """Get current user profile"""
    # Get profile if it exists
    profile = crud.get_user_profile(db, current_user.id)
    user_dict = schemas.User.from_orm(current_user).dict()
    return {**user_dict, "profile": profile}


@router.get("/{user_id}", response_model=schemas.User)
def read_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_user)
):
    """Get user by ID"""
    # Check permissions - only admin or the user themselves can access
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.put("/{user_id}", response_model=schemas.User)
def update_user(
        user_id: int,
        user: schemas.UserUpdate,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_user)
):
    """Update user details"""
    # Check permissions - only admin or the user themselves can update
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.update_user(db=db, user_id=user_id, user=user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
        user_id: int,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(has_role(["admin"]))
):
    """Delete a user (admin only)"""
    crud.delete_user(db=db, user_id=user_id)
    return {"ok": True}


# Profile endpoints
@router.post("/profiles/{user_id}", response_model=schemas.UserProfile, status_code=status.HTTP_201_CREATED)
def create_user_profile(
        user_id: int,
        profile: schemas.UserProfileCreate,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_user)
):
    """Create user profile"""
    # Check permissions - only admin or the user themselves can create
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.create_user_profile(db=db, user_id=user_id, profile=profile)


@router.put("/profiles/{user_id}", response_model=schemas.UserProfile)
def update_user_profile(
        user_id: int,
        profile: schemas.UserProfileUpdate,
        db: Session = Depends(get_db),
        current_user: schemas.User = Depends(get_current_active_user)
):
    """Update user profile"""
    # Check permissions - only admin or the user themselves can update
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return crud.update_user_profile(db=db, user_id=user_id, profile=profile)