# core/lms_core/auth/auth_service.py
from datetime import datetime, timedelta
import os
import secrets
import jwt
from typing import Dict, Optional, Tuple
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from infrastructure.databases.database_config import get_db, get_redis_client
from core.lms_core.users.models import User, Role
from core.lms_core.users.crud import get_user_by_email, get_user_by_username

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-for-development")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION", "1440"))  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days

# Redis key prefix for storing refresh tokens
REFRESH_TOKEN_KEY_PREFIX = "refresh_token:"
# Redis key prefix for storing reset tokens
RESET_TOKEN_KEY_PREFIX = "reset_token:"
# Redis key prefix for storing verification tokens
VERIFICATION_TOKEN_KEY_PREFIX = "verification_token:"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)


async def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username/email and password

    Args:
        db: Database session
        username: Username or email
        password: Plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    # Try to find user by username
    user = get_user_by_username(db, username)

    # If not found, try by email
    if not user:
        user = get_user_by_email(db, username)

    # Verify user exists and password is correct
    if not user or not verify_password(password, user.hashed_password):
        return None

    # Check if user is active
    if not user.is_active:
        return None

    return user


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """
    Create a JWT access token

    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time

    Returns:
        Token string and expiration datetime
    """
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Create token
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return encoded_jwt, expire


def create_refresh_token(user_id: int) -> str:
    """
    Create a refresh token and store in Redis

    Args:
        user_id: User ID

    Returns:
        Refresh token string
    """
    # Generate secure random token
    token = secrets.token_hex(32)

    # Store in Redis with expiration
    redis_client = get_redis_client()
    expiration = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Store token with user ID as value
    redis_client.setex(
        f"{REFRESH_TOKEN_KEY_PREFIX}{token}",
        int(expiration.total_seconds()),
        str(user_id)
    )

    return token


async def validate_refresh_token(token: str) -> Optional[int]:
    """
    Validate a refresh token and return the user ID

    Args:
        token: Refresh token string

    Returns:
        User ID if token is valid, None otherwise
    """
    redis_client = get_redis_client()

    # Check if token exists in Redis
    user_id = redis_client.get(f"{REFRESH_TOKEN_KEY_PREFIX}{token}")

    if user_id:
        return int(user_id)

    return None


async def revoke_refresh_token(token: str) -> bool:
    """
    Revoke a refresh token

    Args:
        token: Refresh token string

    Returns:
        True if token was revoked, False otherwise
    """
    redis_client = get_redis_client()

    # Delete token from Redis
    result = redis_client.delete(f"{REFRESH_TOKEN_KEY_PREFIX}{token}")

    return result > 0


async def revoke_all_user_tokens(user_id: int) -> int:
    """
    Revoke all refresh tokens for a user

    Args:
        user_id: User ID

    Returns:
        Number of tokens revoked
    """
    redis_client = get_redis_client()

    # Find all tokens for this user
    pattern = f"{REFRESH_TOKEN_KEY_PREFIX}*"
    revoked_count = 0

    # Scan through all tokens
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor, pattern, 100)

        for key in keys:
            if redis_client.get(key) == str(user_id):
                redis_client.delete(key)
                revoked_count += 1

        if cursor == 0:
            break

    return revoked_count


async def create_password_reset_token(email: str, db: Session) -> Optional[str]:
    """
    Create a password reset token

    Args:
        email: User email
        db: Database session

    Returns:
        Reset token if user exists, None otherwise
    """
    # Find user by email
    user = get_user_by_email(db, email)

    if not user:
        return None

    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Store in Redis with expiration (24 hours)
    redis_client = get_redis_client()
    expiration = timedelta(hours=24)

    redis_client.setex(
        f"{RESET_TOKEN_KEY_PREFIX}{token}",
        int(expiration.total_seconds()),
        str(user.id)
    )

    return token


async def validate_password_reset_token(token: str) -> Optional[int]:
    """
    Validate a password reset token

    Args:
        token: Reset token string

    Returns:
        User ID if token is valid, None otherwise
    """
    redis_client = get_redis_client()

    # Check if token exists in Redis
    user_id = redis_client.get(f"{RESET_TOKEN_KEY_PREFIX}{token}")

    if user_id:
        return int(user_id)

    return None


async def create_email_verification_token(user_id: int) -> str:
    """
    Create an email verification token

    Args:
        user_id: User ID

    Returns:
        Verification token string
    """
    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Store in Redis with expiration (3 days)
    redis_client = get_redis_client()
    expiration = timedelta(days=3)

    redis_client.setex(
        f"{VERIFICATION_TOKEN_KEY_PREFIX}{token}",
        int(expiration.total_seconds()),
        str(user_id)
    )

    return token


async def validate_email_verification_token(token: str) -> Optional[int]:
    """
    Validate an email verification token

    Args:
        token: Verification token string

    Returns:
        User ID if token is valid, None otherwise
    """
    redis_client = get_redis_client()

    # Check if token exists in Redis
    user_id = redis_client.get(f"{VERIFICATION_TOKEN_KEY_PREFIX}{token}")

    if user_id:
        # Delete token after use
        redis_client.delete(f"{VERIFICATION_TOKEN_KEY_PREFIX}{token}")
        return int(user_id)

    return None


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get the current authenticated user from JWT token

    Args:
        token: JWT token
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Extract user ID
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        # Check token expiration
        expiration = payload.get("exp")
        if expiration is None or datetime.fromtimestamp(expiration) < datetime.utcnow():
            raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current active user

    Args:
        current_user: Current authenticated user

    Returns:
        User object if active

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return current_user


def has_role(required_roles):
    """
    Check if user has any of the required roles

    Args:
        required_roles: List of required role names

    Returns:
        Dependency function to check roles
    """

    async def role_checker(current_user: User = Depends(get_current_active_user)):
        user_roles = [role.name for role in current_user.roles]

        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker