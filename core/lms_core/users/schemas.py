# core/lms_core/users/schemas.py
from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime


# Role schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class Role(RoleBase):
    id: int

    class Config:
        orm_mode = True


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    preferred_language: str = "en"


class UserCreate(UserBase):
    password: str
    roles: List[str] = ["student"]  # Default role

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    preferred_language: Optional[str] = None


class User(UserBase):
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    roles: List[Role] = []

    class Config:
        orm_mode = True


# UserProfile schemas
class UserProfileBase(BaseModel):
    bio: Optional[str] = None
    profile_picture: Optional[str] = None
    timezone: str = "UTC"


class UserProfileCreate(UserProfileBase):
    pass


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


# Combined user with profile
class UserWithProfile(User):
    profile: Optional[UserProfile] = None

    class Config:
        orm_mode = True