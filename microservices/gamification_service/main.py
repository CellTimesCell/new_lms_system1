# Gamification Service for the LMS system
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Dict, Optional
import json
from datetime import datetime

from infrastructure.event_bus.kafka_config import get_kafka_consumer, get_kafka_producer
from infrastructure.databases.database_config import get_db
from microservices.gamification_service.schemas import BadgeAward, AchievementProgress, ProgressUpdate
from microservices.gamification_service.badges.badge_manager import process_badge_award, get_user_badges
from microservices.gamification_service.achievements.achievement_manager import process_achievement_progress, \
    get_user_achievements
from microservices.gamification_service.progress.progress_tracker import update_progress, get_user_progress

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LMS Gamification Service",
    description="Service for managing badges, achievements, and progress tracking",
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

# Event topics
STUDENT_ACTIVITY_TOPIC = "student-activity"
ASSIGNMENT_SUBMITTED_TOPIC = "assignment-submitted"
GRADE_POSTED_TOPIC = "grade-posted"
GAMIFICATION_EVENT_TOPIC = "gamification-events"


@app.post("/badges/award")
async def award_badge(
        badge_award: BadgeAward,
        background_tasks: BackgroundTasks,
        db=Depends(get_db)
):
    """
    Award a badge to a user
    """
    try:
        # Process badge award in background
        background_tasks.add_task(process_badge_award, db, badge_award)

        # Return success response
        return {
            "status": "accepted",
            "message": "Badge award is being processed",
            "badge_id": badge_award.badge_id,
            "user_id": badge_award.user_id
        }
    except Exception as e:
        logger.error(f"Error awarding badge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to award badge")


@app.get("/badges/user/{user_id}")
async def get_badges_for_user(user_id: int, db=Depends(get_db)):
    """
    Get all badges for a user
    """
    try:
        badges = await get_user_badges(db, user_id)
        return badges
    except Exception as e:
        logger.error(f"Error fetching user badges: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch badges")


@app.post("/achievements/progress")
async def update_achievement_progress(
        progress: AchievementProgress,
        background_tasks: BackgroundTasks,
        db=Depends(get_db)
):
    """
    Update progress for an achievement
    """
    try:
        # Process achievement progress in background
        background_tasks.add_task(process_achievement_progress, db, progress)

        # Return success response
        return {
            "status": "accepted",
            "message": "Achievement progress is being updated",
            "achievement_id": progress.achievement_id,
            "user_id": progress.user_id
        }
    except Exception as e:
        logger.error(f"Error updating achievement progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update achievement progress")


@app.get("/achievements/user/{user_id}")
async def get_achievements_for_user(user_id: int, db=Depends(get_db)):
    """
    Get all achievements for a user
    """
    try:
        achievements = await get_user_achievements(db, user_id)
        return achievements
    except Exception as e:
        logger.error(f"Error fetching user achievements: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch achievements")


@app.post("/progress/update")
async def update_user_progress(
        progress_update: ProgressUpdate,
        background_tasks: BackgroundTasks,
        db=Depends(get_db)
):
    """
    Update a user's progress in a course or module
    """
    try:
        # Update progress in background
        background_tasks.add_task(update_progress, db, progress_update)

        # Return success response
        return {
            "status": "accepted",
            "message": "Progress is being updated",
            "user_id": progress_update.user_id,
            "resource_type": progress_update.resource_type,
            "resource_id": progress_update.resource_id
        }
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update progress")


@app.get("/progress/user/{user_id}/course/{course_id}")
async def get_course_progress_for_user(
        user_id: int,
        course_id: int,
        db=Depends(get_db)
):
    """
    Get progress for a user in a specific course
    """
    try:
        progress = await get_user_progress(db, user_id, "course", course_id)
        return progress
    except Exception as e:
        logger.error(f"Error fetching user progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch progress")


# Event listener for student activity (would run in a separate process)
async def consume_student_activity():
    """
    Consume student activity events and process for gamification
    """
    consumer = get_kafka_consumer("gamification-service", [STUDENT_ACTIVITY_TOPIC])

    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            logger.error(f"Consumer error: {msg.error()}")
            continue

        try:
            # Process message
            event_data = json.loads(msg.value().decode('utf-8'))

            # Check for achievements based on activity
            # This would call the appropriate gamification logic
            pass

        except Exception as e:
            logger.error(f"Error processing student activity: {str(e)}")


# Similarly, you would implement consumers for other event types

@app.on_event("startup")
async def startup_event():
    """Start Kafka consumers for gamification events"""
    logger.info("Starting Gamification Service")
    # This would be implemented in separate processes or threads in production


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Shutting down Gamification Service")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)