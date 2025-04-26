# core/lms_core/auth/schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_at: datetime
    user_id: int
    username: str
    roles: List[str]


class TokenData(BaseModel):
    """Token data for validation"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    roles: Optional[List[str]] = None
    exp: Optional[datetime] = None


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordReset(BaseModel):
    """Password reset model"""
    token: str
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class PasswordResetResponse(BaseModel):
    """Password reset response model"""
    message: str


class EmailVerificationRequest(BaseModel):
    """Email verification request model"""
    email: EmailStr


class EmailVerification(BaseModel):
    """Email verification model"""
    token: str


class EmailVerificationResponse(BaseModel):
    """Email verification response model"""
    message: str
    verified: bool


class LoginResponse(BaseModel):
    """Login response model with localization support"""
    access_token: str
    token_type: str
    expires_at: datetime
    user_id: int
    username: str
    roles: List[str]
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferred_language: str = "en"
    messages: Dict[str, str] = {}