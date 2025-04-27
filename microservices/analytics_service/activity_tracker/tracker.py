# microservices/analytics_service/activity_tracker/tracker.py
import logging
import json
import time
from datetime import datetime
import uuid
import asyncio
from typing import Dict, List, Optional, Any

from infrastructure.databases.database_config import get_clickhouse_client
from infrastructure.event_bus.kafka_config import get_kafka_producer, STUDENT_ACTIVITY_TOPIC
from microservices.analytics_service.schemas import ActivityEventCreate
from microservices.analytics_service.models import ActivityEvent

# Initialize logging
logger = logging.getLogger(__name__)


async def track_activity(event: ActivityEventCreate) -> str:
    """
    Track a student activity event

    Args:
        event: The activity event to track

    Returns:
        event_id: The ID of the recorded event
    """
    try:
        # Get ClickHouse client
        ch_client = get_clickhouse_client()

        # Format event data for insertion
        values = (
            event.event_id,
            event.student_id,
            event.event_type,
            event.resource_type,
            event.resource_id,
            event.timestamp.isoformat(),
            event.ip_address,
            event.user_agent,
            event.duration_seconds,
            json.dumps(event.metadata)
        )

        # Insert event into ClickHouse
        query = """
        INSERT INTO activity_events 
        (event_id, student_id, event_type, resource_type, resource_id, timestamp, ip_address, user_agent, duration_seconds, metadata)
        VALUES
        """

        try:
            ch_client.execute(query, [values])
            logger.debug(f"Event {event.event_id} inserted into ClickHouse")
        except Exception as e:
            logger.error(f"Error inserting event into ClickHouse: {str(e)}")
            # Continue to Kafka even if ClickHouse fails

        # Also publish to Kafka for other services to consume
        try:
            producer = get_kafka_producer()

            # Create event message
            event_message = {
                "event_id": event.event_id,
                "student_id": event.student_id,
                "event_type": event.event_type,
                "resource_type": event.resource_type,
                "resource_id": event.resource_id,
                "timestamp": event.timestamp.isoformat(),
                "ip_address": event.ip_address,
                "user_agent": event.user_agent,
                "duration_seconds": event.duration_seconds,
                "metadata": event.metadata
            }

            producer.produce(
                STUDENT_ACTIVITY_TOPIC,
                key=str(event.student_id),
                value=json.dumps(event_message)
            )
            producer.flush()

            logger.debug(f"Event {event.event_id} published to Kafka")
        except Exception as e:
            logger.error(f"Error publishing event to Kafka: {str(e)}")

        logger.info(f"Tracked activity for student {event.student_id}, event: {event.event_type}")

        return event.event_id

    except Exception as e:
        logger.error(f"Error tracking activity: {str(e)}")
        raise


async def track_page_view(
        student_id: int,
        page_url: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        referrer: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track a page view event

    Args:
        student_id: ID of the student
        page_url: URL of the page viewed
        resource_type: Type of resource (course, module, assignment, etc.)
        resource_id: ID of the resource
        ip_address: Client IP address
        user_agent: Client user agent
        session_id: Session ID
        referrer: Referrer URL
        additional_metadata: Additional metadata

    Returns:
        event_id: The ID of the recorded event
    """
    # Create metadata
    metadata = {
        "page_url": page_url,
        "session_id": session_id,
        "referrer": referrer
    }

    # Add additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Create activity event
    event = ActivityEventCreate(
        event_id=str(uuid.uuid4()),
        student_id=student_id,
        event_type="page_view",
        resource_type=resource_type or "page",
        resource_id=resource_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        duration_seconds=0,  # Duration will be updated when the session ends
        metadata=metadata
    )

    # Track the event
    return await track_activity(event)


async def track_resource_access(
        student_id: int,
        resource_type: str,
        resource_id: str,
        action: str = "view",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track a resource access event

    Args:
        student_id: ID of the student
        resource_type: Type of resource (course, module, assignment, etc.)
        resource_id: ID of the resource
        action: Action performed (view, download, etc.)
        ip_address: Client IP address
        user_agent: Client user agent
        session_id: Session ID
        additional_metadata: Additional metadata

    Returns:
        event_id: The ID of the recorded event
    """
    # Create metadata
    metadata = {
        "action": action,
        "session_id": session_id
    }

    # Add additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Create activity event
    event = ActivityEventCreate(
        event_id=str(uuid.uuid4()),
        student_id=student_id,
        event_type="resource_access",
        resource_type=resource_type,
        resource_id=resource_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        duration_seconds=0,
        metadata=metadata
    )

    # Track the event
    return await track_activity(event)


async def track_session_duration(
        student_id: int,
        session_id: str,
        duration_seconds: int,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track session duration

    Args:
        student_id: ID of the student
        session_id: Session ID
        duration_seconds: Duration in seconds
        resource_type: Type of resource (course, module, assignment, etc.)
        resource_id: ID of the resource
        ip_address: Client IP address
        user_agent: Client user agent
        additional_metadata: Additional metadata

    Returns:
        event_id: The ID of the recorded event
    """
    # Create metadata
    metadata = {
        "session_id": session_id
    }

    # Add additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Create activity event
    event = ActivityEventCreate(
        event_id=str(uuid.uuid4()),
        student_id=student_id,
        event_type="session_duration",
        resource_type=resource_type or "session",
        resource_id=resource_id or session_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        duration_seconds=duration_seconds,
        metadata=metadata
    )

    # Track the event
    return await track_activity(event)


async def track_submission_event(
        student_id: int,
        assignment_id: str,
        submission_id: str,
        action: str = "submit",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track a submission event

    Args:
        student_id: ID of the student
        assignment_id: ID of the assignment
        submission_id: ID of the submission
        action: Action performed (submit, update, etc.)
        ip_address: Client IP address
        user_agent: Client user agent
        session_id: Session ID
        additional_metadata: Additional metadata

    Returns:
        event_id: The ID of the recorded event
    """
    # Create metadata
    metadata = {
        "action": action,
        "session_id": session_id,
        "submission_id": submission_id
    }

    # Add additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Create activity event
    event = ActivityEventCreate(
        event_id=str(uuid.uuid4()),
        student_id=student_id,
        event_type="submission",
        resource_type="assignment",
        resource_id=assignment_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        duration_seconds=0,
        metadata=metadata
    )

    # Track the event
    return await track_activity(event)


async def track_quiz_attempt(
        student_id: int,
        quiz_id: str,
        attempt_id: str,
        score: float,
        time_spent: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Track a quiz attempt

    Args:
        student_id: ID of the student
        quiz_id: ID of the quiz
        attempt_id: ID of the attempt
        score: Score achieved
        time_spent: Time spent in seconds
        ip_address: Client IP address
        user_agent: Client user agent
        session_id: Session ID
        additional_metadata: Additional metadata

    Returns:
        event_id: The ID of the recorded event
    """
    # Create metadata
    metadata = {
        "attempt_id": attempt_id,
        "score": score,
        "session_id": session_id
    }

    # Add additional metadata
    if additional_metadata:
        metadata.update(additional_metadata)

    # Create activity event
    event = ActivityEventCreate(
        event_id=str(uuid.uuid4()),
        student_id=student_id,
        event_type="quiz_attempt",
        resource_type="quiz",
        resource_id=quiz_id,
        timestamp=datetime.utcnow(),
        ip_address=ip_address,
        user_agent=user_agent,
        duration_seconds=time_spent,
        metadata=metadata
    )

    # Track the event
    return await track_activity(event)