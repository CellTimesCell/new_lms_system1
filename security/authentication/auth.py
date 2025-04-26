# Authentication service for the LMS system
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import os
from pydantic import BaseModel

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "86400"))  # 24 hours


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_at: datetime
    user_id: int
    username: str
    roles: list


class TokenData(BaseModel):
    """Token data for validation"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    roles: Optional[list] = None
    exp: Optional[datetime] = None


def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)


async def authenticate_user(db, username: str, password: str):
    """Authenticate a user"""
    from core.lms_core.users.crud import get_user_by_username

    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return encoded_jwt, expire


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate token and get current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_data = TokenData(
            user_id=int(user_id),
            username=payload.get("username"),
            roles=payload.get("roles", []),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except jwt.PyJWTError:
        raise credentials_exception

    if token_data.exp < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)):
    """Get current active user"""
    from core.lms_core.users.crud import get_user

    # Get database session
    from infrastructure.databases.database_config import get_db
    db = next(get_db())

    # Get user from database
    user = await get_user(db, user_id=current_user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


def has_role(required_roles):
    """Check if user has required roles"""

    async def role_checker(current_user: TokenData = Depends(get_current_user)):
        if not any(role in current_user.roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker