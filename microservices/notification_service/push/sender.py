# microservices/notification_service/push/sender.py
import logging
import json
import os
import httpx
from typing import Dict, List, Optional

from microservices.notification_service.schemas import PushNotification

# Initialize logging
logger = logging.getLogger(__name__)

# Firebase configuration for push notifications
FIREBASE_SERVER_KEY = os.getenv("FIREBASE_SERVER_KEY")
FIREBASE_API_URL = "https://fcm.googleapis.com/fcm/send"

# Web push configuration
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:admin@yourlms.com")


async def send_push_notification(notification: PushNotification):
    """
    Send a push notification to a user

    Args:
        notification: The push notification to send
    """
    try:
        # Get user device tokens - in a real implementation, this would fetch from a database
        device_tokens = await get_user_device_tokens(notification.recipient_id)

        if not device_tokens:
            logger.info(f"No device tokens found for user {notification.recipient_id}")
            return False

        # Send to each device
        success = False

        for token_info in device_tokens:
            if token_info["type"] == "firebase":
                result = await send_firebase_notification(
                    token_info["token"],
                    notification
                )
                success = success or result
            elif token_info["type"] == "web":
                result = await send_web_push_notification(
                    token_info["token"],
                    notification
                )
                success = success or result

        return success

    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        raise


async def get_user_device_tokens(user_id: int) -> List[Dict]:
    """
    Get device tokens for a user

    Args:
        user_id: User ID

    Returns:
        List of device token information
    """
    # In a real implementation, this would fetch from a database
    # For this example, we'll return a placeholder

    # Simulated database query
    # SELECT device_token, token_type FROM user_devices WHERE user_id = {user_id}

    # Placeholder response
    return [
        {"token": f"firebase_token_{user_id}_1", "type": "firebase"},
        {"token": f"web_push_token_{user_id}_1", "type": "web"}
    ]


async def send_firebase_notification(token: str, notification: PushNotification) -> bool:
    """
    Send a push notification via Firebase Cloud Messaging

    Args:
        token: Device token
        notification: Notification to send

    Returns:
        bool: Whether the notification was sent successfully
    """
    if not FIREBASE_SERVER_KEY:
        logger.warning("Firebase server key not configured, skipping Firebase notification")
        return False

    try:
        # Prepare notification payload
        payload = {
            "to": token,
            "notification": {
                "title": notification.title,
                "body": notification.body,
                "icon": notification.icon,
                "click_action": "OPEN_APP"
            },
            "data": notification.data or {}
        }

        # Add notification ID for tracking
        payload["data"]["notification_id"] = notification.notification_id

        # Send to Firebase
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"key={FIREBASE_SERVER_KEY}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                FIREBASE_API_URL,
                headers=headers,
                json=payload,
                timeout=5.0
            )

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get("success") == 1:
                logger.info(f"Firebase notification sent successfully to {token}")
                return True
            else:
                logger.warning(f"Firebase notification failed: {response_data}")
                return False
        else:
            logger.error(f"Firebase API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error sending Firebase notification: {str(e)}")
        return False


async def send_web_push_notification(subscription_info: str, notification: PushNotification) -> bool:
    """
    Send a web push notification

    Args:
        subscription_info: Web Push subscription information
        notification: Notification to send

    Returns:
        bool: Whether the notification was sent successfully
    """
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        logger.warning("Web Push VAPID keys not configured, skipping Web Push notification")
        return False

    try:
        # Import optional dependency for web push
        from pywebpush import webpush, WebPushException

        # Parse subscription info
        subscription = json.loads(subscription_info)

        # Prepare notification payload
        payload = {
            "title": notification.title,
            "body": notification.body,
            "icon": notification.icon,
            "data": notification.data or {}
        }

        # Add notification ID for tracking
        payload["data"]["notification_id"] = notification.notification_id

        # Send web push notification
        response = webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={
                "sub": VAPID_CLAIM_EMAIL
            }
        )

        if response.status_code == 201:
            logger.info(f"Web Push notification sent successfully")
            return True
        else:
            logger.warning(f"Web Push notification failed: {response.status_code} - {response.text}")
            return False

    except ImportError:
        logger.error("pywebpush package not installed, cannot send Web Push notifications")
        return False
    except Exception as e:
        logger.error(f"Error sending Web Push notification: {str(e)}")
        return False