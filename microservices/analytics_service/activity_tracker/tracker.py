# Student activity tracking module
import json
import logging
from datetime import datetime

from infrastructure.databases.database_config import get_clickhouse_client
from infrastructure.event_bus.kafka_config import get_kafka_producer, STUDENT_ACTIVITY_TOPIC
from microservices.analytics_service.schemas import ActivityEventCreate

# Initialize logging
logger = logging.getLogger(__name__)


async def track_activity(event: ActivityEventCreate):
    """
    Track a student activity event

    Args:
        event: The activity event to track
    """
    try:
        # Get ClickHouse client
        ch_client = get_clickhouse_client()

        # Insert event into ClickHouse
        query = """
        INSERT INTO activity_events 
        (event_id, student_id, event_type, resource_type, resource_id, timestamp, ip_address, user_agent, duration_seconds, metadata)
        VALUES
        """

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

        # Execute the query
        ch_client.execute(query, [values])

        # Also publish to Kafka for other services to consume
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

        # Publish to Kafka
        producer.produce(
            STUDENT_ACTIVITY_TOPIC,
            key=str(event.student_id),
            value=json.dumps(event_message)
        )
        producer.flush()

        logger.info(f"Tracked activity for student {event.student_id}, event: {event.event_type}")

        return event.event_id

    except Exception as e:
        logger.error(f"Error tracking activity: {str(e)}")
        raise