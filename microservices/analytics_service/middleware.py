# microservices/analytics_service/middleware.py
from fastapi import Request
import time
import uuid
import json
import httpx
from datetime import datetime


async def activity_tracking_middleware(request: Request, call_next):
    """Middleware to track user activity"""
    # Skip tracking for certain endpoints
    if request.url.path.startswith(("/health", "/metrics", "/api/analytics")):
        return await call_next(request)

    # Get start time
    start_time = time.time()

    # Process the request
    response = await call_next(request)

    # Only track authenticated requests
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return response

    # Extract user info if possible
    user_id = None
    try:
        # In a real implementation, this would decode the JWT
        # For now, we'll assume we can get the user_id from somewhere
        user_id = 1  # Placeholder
    except:
        return response

    # Calculate request duration
    duration = time.time() - start_time

    # Determine resource type and ID
    path_parts = request.url.path.strip("/").split("/")
    resource_type = path_parts[1] if len(path_parts) > 1 else "other"
    resource_id = path_parts[2] if len(path_parts) > 2 else None

    # Create activity event
    event = {
        "event_id": str(uuid.uuid4()),
        "student_id": user_id,
        "event_type": request.method,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "timestamp": datetime.utcnow().isoformat(),
        "ip_address": request.client.host,
        "user_agent": request.headers.get("User-Agent", ""),
        "duration_seconds": duration,
        "metadata": {
            "status_code": response.status_code,
            "path": str(request.url.path),
            "query_params": str(request.query_params)
        }
    }

    # Send event to analytics service asynchronously
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://analytics-service:8000/activity/track",
                json=event,
                timeout=1.0  # Short timeout to not block the response
            )
    except:
        # Don't fail the request if tracking fails
        pass

    return response