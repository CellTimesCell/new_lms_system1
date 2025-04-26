# core/lms_core/auth/router.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime, timedelta
import secrets
import os

from infrastructure.databases.database_config import get_db
from core.lms_core.users.models import User
from core.lms_core.auth import schemas
from core.lms_core.auth.auth import (
    authenticate_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_password_hash
)
from core.lms_core.auth.email import send_password_reset_email

router = APIRouter()


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, expire = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    # Get user roles
    roles = [role.name for role in user.roles]

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expire.isoformat(),
        "user_id": user.id,
        "username": user.username,
        "roles": roles
    }


@router.post("/request-password-reset", response_model=schemas.PasswordResetResponse)
async def request_password_reset(
        request_data: schemas.PasswordResetRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    """Request a password reset token"""
    # Find user by email
    user = db.query(User).filter(User.email == request_data.email).first()

    # Always return success, even if user not found (security best practice)
    if not user:
        return {"message": "If the email is registered, a password reset link will be sent."}

    # Generate token
    reset_token = secrets.token_urlsafe(32)

    # Store token in database with expiration time (24 hours)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=24)
    db.commit()

    # Send email in background
    base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_url = f"{base_url}/reset-password/{reset_token}"

    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.username,
        reset_url
    )

    return {"message": "If the email is registered, a password reset link will be sent."}


@router.post("/reset-password", response_model=schemas.PasswordResetResponse)
async def reset_password(
        reset_data: schemas.PasswordReset,
        db: Session = Depends(get_db)
):
    """Reset user password using token"""
    # Find user by token
    user = db.query(User).filter(User.reset_token == reset_data.token).first()

    # Validate token
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    # Check if token has expired
    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired"
        )

    # Update password
    user.hashed_password = get_password_hash(reset_data.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Password has been reset successfully"}