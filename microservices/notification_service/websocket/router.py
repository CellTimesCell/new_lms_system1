# microservices/notification_service/websocket/router.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
import logging
import json
from typing import Dict, List, Optional
import jwt
import os

from microservices.notification_service.websocket.handler import notification_manager

# Initialize logging
logger = logging.getLogger(__name__)

# JWT Configuration for WebSocket Authentication
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret-key-for-development")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

router = APIRouter()


async def get_user_from_token(token: str) -> Dict:
    """
    Validate JWT token and return user information

    Args:
        token: JWT token

    Returns:
        Dict: User information

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return {"user_id": int(user_id), "username": username}

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time notifications
    """
    # Wait for connection
    await websocket.accept()

    try:
        # Receive and validate authentication message
        auth_message = await websocket.receive_text()
        auth_data = json.loads(auth_message)

        if "token" not in auth_data:
            await websocket.send_text(json.dumps({"error": "Authentication required"}))
            await websocket.close(code=1008)  # Policy violation
            return

        # Validate token
        try:
            user = await get_user_from_token(auth_data["token"])
            user_id = user["user_id"]
        except HTTPException:
            await websocket.send_text(json.dumps({"error": "Invalid token"}))
            await websocket.close(code=1008)  # Policy violation
            return

        # Send acknowledgment
        await websocket.send_text(json.dumps({"status": "connected", "user_id": user_id}))

        # Register connection
        await notification_manager.connect(websocket, user_id)

        # Handle incoming messages
        try:
            while True:
                # Wait for any incoming messages (like ping/pong or status updates)
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "status":
                    # Update user status if provided
                    status = message.get("status")
                    if status in ["away", "busy", "online"]:
                        # In a real implementation, you would update the user's status
                        pass

        except WebSocketDisconnect:
            # Handle disconnection
            await notification_manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011)  # Internal error


@router.get("/notifications/status/{user_id}")
async def get_user_status(user_id: int):
    """
    Get a user's online status
    """
    status = notification_manager.get_user_status(user_id)
    return {"user_id": user_id, "status": status}


@router.get("/notifications/online-users")
async def get_online_users():
    """
    Get a list of all online users
    """
    online_users = notification_manager.get_online_users()
    return {"online_users": online_users, "count": len(online_users)}