# core/lms_core/auth/router.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import json
import os

from infrastructure.databases.database_config import get_db
from core.lms_core.users.crud import get_user, get_user_by_email, update_user, create_user_if_not_exists
from core.lms_core.users.schemas import UserCreate
from core.lms_core.auth.schemas import (
    Token, TokenData, RefreshToken, PasswordResetRequest, PasswordReset,
    EmailVerificationRequest, EmailVerification, LoginResponse
)
from core.lms_core.auth.auth_service import (
    authenticate_user, create_access_token, create_refresh_token,
    validate_refresh_token, revoke_refresh_token, revoke_all_user_tokens,
    create_password_reset_token, validate_password_reset_token,
    create_email_verification_token, validate_email_verification_token,
    get_current_active_user, get_password_hash
)
from core.lms_core.auth.email import send_password_reset_email, send_verification_email

router = APIRouter()


@router.post("/token", response_model=LoginResponse)
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # Authenticate user
    user = await authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=int(os.getenv("JWT_EXPIRATION", "1440")))

    # Get user roles
    roles = [role.name for role in user.roles]

    # Create tokens
    access_token, expire = create_access_token(
        data={"sub": str(user.id), "username": user.username, "roles": roles},
        expires_delta=access_token_expires
    )

    refresh_token = create_refresh_token(user.id)

    # Create response
    response = {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expire,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "roles": roles,
        "preferred_language": user.preferred_language,
        "messages": {}
    }

    # Add localized messages if needed (based on user's preferred language)
    if user.preferred_language == "es":
        response["messages"] = {
            "welcome": f"¡Bienvenido de nuevo, {user.first_name}!",
            "login_success": "Inicio de sesión exitoso"
        }
    else:
        response["messages"] = {
            "welcome": f"Welcome back, {user.first_name}!",
            "login_success": "Login successful"
        }

    return response


@router.post("/refresh", response_model=Token)
async def refresh_token(
        token_data: RefreshToken,
        db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Validate refresh token
    user_id = await validate_refresh_token(token_data.refresh_token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user
    user = get_user(db, user_id)

    if not user or not user.is_active:
        # Revoke refresh token if user no longer exists or is inactive
        await revoke_refresh_token(token_data.refresh_token)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new access token
    roles = [role.name for role in user.roles]

    access_token, expire = create_access_token(
        data={"sub": str(user.id), "username": user.username, "roles": roles}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expire,
        "user_id": user.id,
        "username": user.username,
        "roles": roles
    }


@router.post("/logout")
async def logout(
        token_data: RefreshToken,
        current_user=Depends(get_current_active_user)
):
    """
    Logout user and revoke refresh token
    """
    # Revoke the provided refresh token
    revoked = await revoke_refresh_token(token_data.refresh_token)

    return {"success": True, "message": "Logout successful"}


@router.post("/logout-all-devices")
async def logout_all_devices(
        current_user=Depends(get_current_active_user)
):
    """
    Logout from all devices and revoke all refresh tokens
    """
    # Revoke all refresh tokens for the user
    revoked_count = await revoke_all_user_tokens(current_user.id)

    return {
        "success": True,
        "message": f"Logged out from all devices ({revoked_count} sessions)"
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
        user_data: UserCreate,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    # Create user
    user = create_user_if_not_exists(db, user_data)

    # Create email verification token
    verification_token = await create_email_verification_token(user.id)

    # Generate verification URL
    base_url = os.getenv("FRONTEND_URL", request.base_url)
    verification_url = f"{base_url}verify-email/{verification_token}"

    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.username,
        verification_url
    )

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "message": "User registered successfully. Please check your email to verify your account."
    }


@router.post("/request-password-reset")
async def request_password_reset(
        request_data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Request a password reset token
    """
    # Create reset token (only if user exists)
    reset_token = await create_password_reset_token(request_data.email, db)

    # Always return success to prevent email enumeration
    if not reset_token:
        return {"message": "If your email is registered, a password reset link will be sent."}

    # Generate reset URL
    base_url = os.getenv("FRONTEND_URL", request.base_url)
    reset_url = f"{base_url}reset-password/{reset_token}"

    # Get user
    user = get_user_by_email(db, request_data.email)

    # Send reset email in background
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.username,
        reset_url
    )

    return {"message": "If your email is registered, a password reset link will be sent."}


@router.post("/reset-password")
async def reset_password(
        reset_data: PasswordReset,
        db: Session = Depends(get_db)
):
    """
    Reset user password using token
    """
    # Validate reset token
    user_id = await validate_password_reset_token(reset_data.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    # Get user
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    # Update password
    update_data = {"hashed_password": get_password_hash(reset_data.password)}
    update_user(db, user_id, update_data)

    # Revoke all refresh tokens for security
    await revoke_all_user_tokens(user_id)

    return {"message": "Password has been reset successfully"}


@router.post("/verify-email")
async def verify_email(
        verification_data: EmailVerification,
        db: Session = Depends(get_db)
):
    """
    Verify email address using token
    """
    # Validate verification token
    user_id = await validate_email_verification_token(verification_data.token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    # Get user
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    # Update user verification status
    update_data = {"is_verified": True}
    update_user(db, user_id, update_data)

    return {
        "message": "Email verified successfully",
        "verified": True
    }


@router.post("/resend-verification")
async def resend_verification_email(
        request_data: EmailVerificationRequest,
        background_tasks: BackgroundTasks,
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Resend verification email
    """
    # Find user by email
    user = get_user_by_email(db, request_data.email)

    # Always return success to prevent email enumeration
    if not user:
        return {"message": "If your email is registered, a verification link will be sent."}

    # Check if already verified
    if user.is_verified:
        return {"message": "Your email is already verified."}

    # Create verification token
    verification_token = await create_email_verification_token(user.id)

    # Generate verification URL
    base_url = os.getenv("FRONTEND_URL", request.base_url)
    verification_url = f"{base_url}verify-email/{verification_token}"

    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.username,
        verification_url
    )

    return {"message": "If your email is registered, a verification link will be sent."}


@router.get("/me")
async def get_current_user_info(
        current_user=Depends(get_current_active_user)
):
    """
    Get current user information
    """
    # Get user roles
    roles = [role.name for role in current_user.roles]

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "roles": roles,
        "preferred_language": current_user.preferred_language
    }