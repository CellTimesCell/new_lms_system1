# Notification Service for the LMS system
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Dict, Optional
import os
import json
import asyncio
from datetime import datetime

from infrastructure.event_bus.kafka_config import get_kafka_consumer, get_kafka_producer, NOTIFICATION_TOPIC
from microservices.notification_service.email.sender import send_email
from microservices.notification_service.push.sender import send_push_notification
from microservices.notification_service.schemas import EmailNotification, PushNotification, WebSocketNotification

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LMS Notification Service",
    description="Service for sending notifications to users",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connected WebSocket clients
connected_clients = {}


@app.post("/notifications/email")
async def send_email_notification(
        notification: EmailNotification,
        background_tasks: BackgroundTasks
):
    """
    Send an email notification
    """
    try:
        # Send email in background
        background_tasks.add_task(send_email, notification)

        # Also publish to Kafka for tracking
        producer = get_kafka_producer()
        producer.produce(
            NOTIFICATION_TOPIC,
            key=str(notification.recipient_id),
            value=json.dumps({
                "type": "email",
                "recipient_id": notification.recipient_id,
                "subject": notification.subject,
                "timestamp": datetime.utcnow().isoformat(),
                "notification_id": notification.notification_id
            })
        )
        producer.flush()

        return {"status": "accepted", "notification_id": notification.notification_id}

    except Exception as e:
        logger.error(f"Error sending email notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email notification")


@app.post("/notifications/push")
async def send_push_notification_endpoint(
        notification: PushNotification,
        background_tasks: BackgroundTasks
):
    """
    Send a push notification
    """
    try:
        # Send push notification in background
        background_tasks.add_task(send_push_notification, notification)

        # Also publish to Kafka for tracking
        producer = get_kafka_producer()
        producer.produce(
            NOTIFICATION_TOPIC,
            key=str(notification.recipient_id),
            value=json.dumps({
                "type": "push",
                "recipient_id": notification.recipient_id,
                "title": notification.title,
                "timestamp": datetime.utcnow().isoformat(),
                "notification_id": notification.notification_id
            })
        )
        producer.flush()

        return {"status": "accepted", "notification_id": notification.notification_id}

    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send push notification")


@app.post("/notifications/websocket")
async def send_websocket_notification(notification: WebSocketNotification):
    """
    Send a real-time WebSocket notification
    """
    try:
        # Check if user is connected
        if notification.recipient_id in connected_clients:
            # Send notification through WebSocket
            await connected_clients[notification.recipient_id].send_text(
                json.dumps({
                    "type": notification.notification_type,
                    "title": notification.title,
                    "message": notification.message,
                    "data": notification.data
                })
            )

            # Also publish to Kafka for tracking
            producer = get_kafka_producer()
            producer.produce(
                NOTIFICATION_TOPIC,
                key=str(notification.recipient_id),
                value=json.dumps({
                    "type": "websocket",
                    "recipient_id": notification.recipient_id,
                    "title": notification.title,
                    "timestamp": datetime.utcnow().isoformat(),
                    "notification_id": notification.notification_id
                })
            )
            producer.flush()

            return {"status": "sent", "notification_id": notification.notification_id}
        else:
            return {"status": "queued", "notification_id": notification.notification_id,
                    "message": "User not connected, notification queued"}

    except Exception as e:
        logger.error(f"Error sending WebSocket notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send WebSocket notification")


@app.post("/notifications/bulk")
async def send_bulk_notifications(
        user_ids: List[int],
        notification_template: Dict,
        notification_type: str,
        background_tasks: BackgroundTasks
):
    """
    Send bulk notifications to multiple users
    """
    try:
        # Process bulk notifications in background
        background_tasks.add_task(process_bulk_notifications, user_ids, notification_template, notification_type)

        return {
            "status": "accepted",
            "message": f"Processing {len(user_ids)} {notification_type} notifications"
        }

    except Exception as e:
        logger.error(f"Error sending bulk notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start bulk notification process")


async def process_bulk_notifications(user_ids, template, notification_type):
    """
    Process bulk notifications in background
    """
    # In a real implementation, this would batch the notifications
    # and handle rate limiting for external services
    pass


@app.on_event("startup")
async def startup_event():
    """Start Kafka consumer for notification events"""
    logger.info("Starting Notification Service")
    # This would be implemented in a separate process or thread in production


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Shutting down Notification Service")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)