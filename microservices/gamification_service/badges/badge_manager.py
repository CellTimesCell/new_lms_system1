# Badge manager for the LMS gamification system
import logging
from datetime import datetime
from typing import List, Dict, Optional
import json

from infrastructure.event_bus.kafka_config import get_kafka_producer, GAMIFICATION_EVENT_TOPIC

# Initialize logging
logger = logging.getLogger(__name__)


async def process_badge_award(db, badge_award):
    """
    Process a badge award

    Args:
        db: Database session
        badge_award: BadgeAward object
    """
    try:
        # Check if user already has this badge
        existing_badge = await db.execute(
            """
            SELECT id FROM user_badges 
            WHERE user_id = :user_id AND badge_id = :badge_id
            """,
            {"user_id": badge_award.user_id, "badge_id": badge_award.badge_id}
        )

        if existing_badge.fetchone():
            logger.info(f"User {badge_award.user_id} already has badge {badge_award.badge_id}")
            return

        # Get badge details
        badge = await db.execute(
            """
            SELECT id, name, description, image_url FROM badges
            WHERE id = :badge_id
            """,
            {"badge_id": badge_award.badge_id}
        )

        badge_row = badge.fetchone()
        if not badge_row:
            logger.error(f"Badge {badge_award.badge_id} not found")
            return

        # Award badge to user
        await db.execute(
            """
            INSERT INTO user_badges (user_id, badge_id, awarded_at, awarded_by, reason)
            VALUES (:user_id, :badge_id, :awarded_at, :awarded_by, :reason)
            """,
            {
                "user_id": badge_award.user_id,
                "badge_id": badge_award.badge_id,
                "awarded_at": datetime.utcnow(),
                "awarded_by": badge_award.awarded_by,
                "reason": badge_award.reason
            }
        )

        await db.commit()

        # Publish event for notification system
        producer = get_kafka_producer()

        event_message = {
            "event_type": "badge_awarded",
            "user_id": badge_award.user_id,
            "badge_id": badge_award.badge_id,
            "badge_name": badge_row[1],  # name
            "badge_description": badge_row[2],  # description
            "badge_image_url": badge_row[3],  # image_url
            "timestamp": datetime.utcnow().isoformat(),
            "reason": badge_award.reason
        }

        producer.produce(
            GAMIFICATION_EVENT_TOPIC,
            key=str(badge_award.user_id),
            value=json.dumps(event_message)
        )
        producer.flush()

        logger.info(f"Badge {badge_award.badge_id} awarded to user {badge_award.user_id}")

    except Exception as e:
        logger.error(f"Error awarding badge: {str(e)}")
        await db.rollback()
        raise


async def get_user_badges(db, user_id):
    """
    Get all badges for a user

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of badge objects
    """
    try:
        # Get user badges
        result = await db.execute(
            """
            SELECT b.id, b.name, b.description, b.image_url, b.category, 
                   ub.awarded_at, ub.reason
            FROM badges b
            JOIN user_badges ub ON b.id = ub.badge_id
            WHERE ub.user_id = :user_id
            ORDER BY ub.awarded_at DESC
            """,
            {"user_id": user_id}
        )

        badges = []
        for row in result.fetchall():
            badges.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "image_url": row[3],
                "category": row[4],
                "awarded_at": row[5].isoformat() if row[5] else None,
                "reason": row[6]
            })

        return badges

    except Exception as e:
        logger.error(f"Error fetching user badges: {str(e)}")
        raise