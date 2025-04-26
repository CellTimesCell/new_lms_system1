# Analytics Service for student activity tracking and reporting
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime, timedelta

from infrastructure.databases.database_config import get_clickhouse_client
from infrastructure.event_bus.kafka_config import get_kafka_consumer, STUDENT_ACTIVITY_TOPIC
from microservices.analytics_service.models import ActivityEvent, ActivityReport
from microservices.analytics_service.schemas import ActivityEventCreate, ReportRequest
from microservices.analytics_service.activity_tracker.tracker import track_activity
from microservices.analytics_service.report_generator.generator import generate_report

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LMS Analytics Service",
    description="Service for tracking student activity and generating reports",
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


# Dependency for ClickHouse client
def get_ch_client():
    return get_clickhouse_client()


@app.post("/activity/track")
async def record_activity(event: ActivityEventCreate, background_tasks: BackgroundTasks):
    """
    Record student activity event

    This endpoint receives activity events from frontend or core API
    and stores them in ClickHouse for analytics
    """
    try:
        # Process activity in background
        background_tasks.add_task(track_activity, event)
        return {"status": "accepted", "message": "Activity is being processed"}
    except Exception as e:
        logger.error(f"Error recording activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record activity")


@app.get("/activity/student/{student_id}")
async def get_student_activity(
        student_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        ch_client=Depends(get_ch_client)
):
    """
    Get activity history for a specific student
    """
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    query = f"""
    SELECT event_type, resource_type, resource_id, timestamp, duration_seconds, metadata
    FROM activity_events
    WHERE student_id = {student_id}
    AND timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    ORDER BY timestamp DESC
    """

    try:
        results = ch_client.execute(query)
        events = [
            {
                "event_type": row[0],
                "resource_type": row[1],
                "resource_id": row[2],
                "timestamp": row[3],
                "duration_seconds": row[4],
                "metadata": row[5]
            }
            for row in results
        ]
        return events
    except Exception as e:
        logger.error(f"Error fetching student activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity data")


@app.get("/activity/course/{course_id}")
async def get_course_activity(
        course_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        ch_client=Depends(get_ch_client)
):
    """
    Get activity statistics for a course
    """
    # Set default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    # Get overall activity stats
    query = f"""
    SELECT 
        toDate(timestamp) as date,
        count() as event_count,
        count(distinct student_id) as active_students,
        sum(duration_seconds) as total_duration
    FROM activity_events
    WHERE resource_type = 'course'
    AND resource_id = {course_id}
    AND timestamp BETWEEN '{start_date.isoformat()}' AND '{end_date.isoformat()}'
    GROUP BY date
    ORDER BY date
    """

    try:
        results = ch_client.execute(query)
        stats = [
            {
                "date": row[0].strftime("%Y-%m-%d"),
                "event_count": row[1],
                "active_students": row[2],
                "total_duration_hours": round(row[3] / 3600, 2)
            }
            for row in results
        ]
        return stats
    except Exception as e:
        logger.error(f"Error fetching course activity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity data")


@app.post("/reports/generate")
async def create_report(
        report_request: ReportRequest,
        background_tasks: BackgroundTasks
):
    """
    Generate a custom analytics report
    """
    try:
        # Generate report in background
        report_id = background_tasks.add_task(generate_report, report_request)
        return {
            "status": "accepted",
            "message": "Report generation started",
            "report_id": report_id
        }
    except Exception as e:
        logger.error(f"Error initiating report generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start report generation")


@app.get("/reports/{report_id}")
async def get_report(report_id: str, ch_client=Depends(get_ch_client)):
    """
    Get a generated report by ID
    """
    query = f"""
    SELECT report_id, report_type, parameters, status, created_at, completed_at, result_url
    FROM reports
    WHERE report_id = '{report_id}'
    """

    try:
        results = ch_client.execute(query)
        if not results:
            raise HTTPException(status_code=404, detail="Report not found")

        row = results[0]
        report = {
            "report_id": row[0],
            "report_type": row[1],
            "parameters": row[2],
            "status": row[3],
            "created_at": row[4],
            "completed_at": row[5],
            "result_url": row[6]
        }
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch report data")


@app.on_event("startup")
async def startup_event():
    """Start Kafka consumer for activity events"""
    logger.info("Starting Analytics Service")
    # This would be implemented in a separate process or thread in production


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Shutting down Analytics Service")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)