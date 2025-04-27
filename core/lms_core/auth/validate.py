# core/lms_core/auth/validate.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from typing import Optional
import jwt
import os
from datetime import datetime

from infrastructure.databases.database_config import get_db
from core.lms_core.users.models import User

router = APIRouter()

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-for-development")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


@router.get("/validate")
async def validate_token(
        request: Request,
        authorization: Optional[str] = Header(None)
):
    """
    Validate JWT token for Traefik Forward Auth

    This endpoint is used by Traefik to validate requests
    before forwarding them to the actual services.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # Extract token
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Decode and validate token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Extract user data
        user_id = payload.get("sub")
        username = payload.get("username")
        roles = payload.get("roles", [])
        exp = payload.get("exp")

        # Check token expiration
        if not exp or datetime.fromtimestamp(exp) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Set user info in response headers
        response_headers = {
            "X-User-Id": str(user_id),
            "X-User-Name": username,
            "X-User-Role": ",".join(roles)
        }

        # Return 200 OK with user headers
        return {"authenticated": True, "user_id": user_id, "roles": roles}

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"}
        )