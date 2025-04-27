# microservices/notification_service/websocket/handler.py
import logging
import json
import asyncio
from typing import Dict, List, Optional, Set, Union
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import uuid

from infrastructure.databases.database_config import get_redis_client

# Initialize logging
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket connection manager for real-time notifications
    """

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.user_status: Dict[int, Dict] = {}
        self.redis = get_redis_client()

    async def connect(self, websocket: WebSocket, user_id: int):
        """
        Connect a WebSocket client

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        # Store connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        # Update user status
        self.user_status[user_id] = {
            "status": "online",
            "last_seen": datetime.utcnow().isoformat(),
            "connection_count": len(self.active_connections[user_id])
        }

        # Store in Redis for distributed deployment
        self.redis.hset(
            f"user:status:{user_id}",
            mapping=self.user_status[user_id]
        )

        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "message": "Connected to notification service",
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Send queued notifications
        await self.send_queued_notifications(user_id, websocket)

        logger.info(
            f"User {user_id} connected to WebSocket, total connections: {len(self.active_connections[user_id])}")

    async def disconnect(self, websocket: WebSocket, user_id: int):
        """
        Disconnect a WebSocket client

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        # Remove connection
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Update status if no connections left
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Update user status
                self.user_status[user_id] = {
                    "status": "offline",
                    "last_seen": datetime.utcnow().isoformat(),
                    "connection_count": 0
                }

                # Update in Redis
                self.redis.hset(
                    f"user:status:{user_id}",
                    mapping=self.user_status[user_id]
                )
            else:
                # Update connection count
                self.user_status[user_id]["connection_count"] = len(self.active_connections[user_id])

                # Update in Redis
                self.redis.hset(
                    f"user:status:{user_id}",
                    "connection_count",
                    len(self.active_connections[user_id])
                )

        logger.info(f"User {user_id} disconnected from WebSocket")

    async def send_personal_message(self, message: dict, user_id: int) -> bool:
        """
        Send a message to a specific user

        Args:
            message: Message to send (will be JSON-encoded)
            user_id: User ID

        Returns:
            bool: True if message was sent to at least one connection
        """
        # Add message ID and timestamp if not present
        if "id" not in message:
            message["id"] = str(uuid.uuid4())

        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        if user_id not in self.active_connections or not self.active_connections[user_id]:
            # Queue message for later delivery
            await self.queue_notification(user_id, message)
            logger.debug(f"User {user_id} not connected, message queued: {message['id']}")
            return False

        # Encode message as JSON
        message_json = json.dumps(message)

        # Track successful sends
        success = False
        failed_connections = set()

        # Send to all connections for this user
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_text(message_json)
                success = True
                logger.debug(f"Message {message['id']} sent to user {user_id}")
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                failed_connections.add(websocket)

        # Clean up failed connections
        for websocket in failed_connections:
            self.active_connections[user_id].discard(websocket)

        # Update connection count if any failed
        if failed_connections:
            self.user_status[user_id]["connection_count"] = len(self.active_connections[user_id])

            # Update in Redis
            self.redis.hset(
                f"user:status:{user_id}",
                "connection_count",
                len(self.active_connections[user_id])
            )

            # If all connections failed, queue the message
            if not success:
                await self.queue_notification(user_id, message)
                logger.debug(f"All connections failed for user {user_id}, message queued: {message['id']}")

        return success

    async def broadcast(self, message: dict, users: List[int]) -> Dict[int, bool]:
        """
        Broadcast a message to multiple users

        Args:
            message: Message to send (will be JSON-encoded)
            users: List of user IDs

        Returns:
            Dict[int, bool]: Map of user IDs to success status
        """
        # Add message ID and timestamp if not present
        if "id" not in message:
            message["id"] = str(uuid.uuid4())

        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()

        results = {}

        # Send to each user
        for user_id in users:
            try:
                success = await self.send_personal_message(message, user_id)
                results[user_id] = success
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                results[user_id] = False

        return results

    async def queue_notification(self, user_id: int, message: dict):
        """
        Queue a notification for offline users

        Args:
            user_id: User ID
            message: Message to queue
        """
        # Use Redis to store queued notifications
        notification_key = f"user:notifications:{user_id}"

        # Store message as JSON string
        self.redis.lpush(notification_key, json.dumps(message))

        # Set TTL for queued notifications (30 days)
        self.redis.expire(notification_key, 60 * 60 * 24 * 30)

        logger.debug(f"Notification queued for user {user_id}: {message['id']}")

    async def send_queued_notifications(self, user_id: int, websocket: Optional[WebSocket] = None):
        """
        Send queued notifications to a user

        Args:
            user_id: User ID
            websocket: Specific WebSocket to send to (optional)
        """
        # Get queued notifications from Redis
        notification_key = f"user:notifications:{user_id}"

        # Check if there are any queued notifications
        queue_length = self.redis.llen(notification_key)

        if queue_length > 0:
            logger.info(f"Sending {queue_length} queued notifications to user {user_id}")

            # Get all queued notifications
            notifications = self.redis.lrange(notification_key, 0, -1)

            # Send each notification
            for notification_json in notifications:
                try:
                    notification = json.loads(notification_json)

                    # Set "queued" flag
                    notification["queued"] = True

                    # Send notification
                    if websocket:
                        await websocket.send_text(json.dumps(notification))
                    else:
                        # Skip queueing if sending fails
                        for conn in self.active_connections.get(user_id, set()):
                            try:
                                await conn.send_text(json.dumps(notification))
                            except Exception as e:
                                logger.error(f"Error sending queued notification: {str(e)}")

                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON in queued notification for user {user_id}")
                except Exception as e:
                    logger.error(f"Error processing queued notification: {str(e)}")

            # Delete the notifications from the queue
            self.redis.delete(notification_key)

    def get_user_status(self, user_id: int) -> Dict:
        """
        Get a user's online status

        Args:
            user_id: User ID

        Returns:
            Dict: User status information
        """
        # Check local status first
        if user_id in self.user_status:
            return self.user_status[user_id]

        # Check Redis for distributed deployment
        status = self.redis.hgetall(f"user:status:{user_id}")

        if status:
            # Convert from bytes to string
            return {k.decode(): v.decode() for k, v in status.items()}

        # Default status if not found
        return {
            "status": "unknown",
            "last_seen": None,
            "connection_count": 0
        }

    def get_online_users(self) -> List[int]:
        """
        Get a list of all online users

        Returns:
            List[int]: List of online user IDs
        """
        # Local connections
        local_online = list(self.active_connections.keys())

        # Check Redis for other instances
        # In a real distributed deployment, you would use Redis to track all online users
        # This is a simplified implementation

        return local_online

    async def update_user_status(self, user_id: int, status: str):
        """
        Update a user's status

        Args:
            user_id: User ID
            status: New status (online, away, busy, offline)
        """
        # Valid statuses
        valid_statuses = ["online", "away", "busy", "offline"]

        if status not in valid_statuses:
            logger.warning(f"Invalid status '{status}' for user {user_id}")
            return

        # Check if user exists
        if user_id in self.user_status:
            # Update status
            self.user_status[user_id]["status"] = status
            self.user_status[user_id]["last_seen"] = datetime.utcnow().isoformat()

            # Update in Redis
            self.redis.hset(
                f"user:status:{user_id}",
                mapping={
                    "status": status,
                    "last_seen": datetime.utcnow().isoformat()
                }
            )

            logger.info(f"User {user_id} status updated to '{status}'")


# Create global instance
connection_manager = ConnectionManager()