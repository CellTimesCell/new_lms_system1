# Notification schemas
from pydantic import BaseModel
from typing import Dict, Optional, Any, List
from datetime import datetime
import uuid


class NotificationBase(BaseModel):
    """Base notification schema"""
    recipient_id: int
    notification_type: str
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool = False


class NotificationCreate(NotificationBase):
    """Schema for creating notifications"""
    notification_id: str = str(uuid.uuid4())


class Notification(NotificationBase):
    """Schema for notification response"""
    id: int
    notification_id: str
    created_at: datetime

    class Config:
        orm_mode = True


class EmailNotification(BaseModel):
    """Schema for email notifications"""
    recipient_id: int
    recipient_email: str
    subject: str
    body: str
    notification_id: str = str(uuid.uuid4())
    html_body: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class PushNotification(BaseModel):
    """Schema for push notifications"""
    recipient_id: int
    title: str
    body: str
    notification_id: str = str(uuid.uuid4())
    icon: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WebSocketNotification(BaseModel):
    """Schema for websocket notifications"""
    recipient_id: int
    notification_type: str
    title: str
    message: str
    notification_id: str = str(uuid.uuid4())
    data: Optional[Dict[str, Any]] = None