# microservices/analytics_service/report_router.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from datetime import datetime, timedelta

from infrastructure.databases.database_config import get_clickhouse_client
from microservices.analytics_service.schemas import (
    ReportRequest,
    ReportResponse,
    ReportType
)
from microservices.analytics_service.report_generator.generator import generate_report
from security.authentication.auth import get_current_active_user, has_role

router = APIRouter()


@router.post("/reports", response_model=ReportResponse)
async def create_report(
        request: ReportRequest,
        background_tasks: BackgroundTasks,
        current_user=Depends(has_role(["admin", "instructor"]))
):
    """
    Generate a new analytics report
    """
    try:
        # Add current user ID as creator
        request.created_by = current_user.id

        # Validate permissions based on report type
        if request.report_type == ReportType.STUDENT_ACTIVITY:
            student_id = request.parameters.get('student_id')
            # If not an admin, instructors can only view reports for their students
            if "admin" not in [role.name for role in current_user.roles]:
                # In a real implementation, you would check if the student is in a course taught by this instructor
                pass

        # Generate report in background
        report_id = await generate_report(request)

        # Get initial report status
        ch_client = get_clickhouse_client()
        query = f"""
        SELECT report_id, report_type, status, created_at
        FROM reports
        WHERE report_id = '{report_id}'
        """

        results = ch_client.execute(query)
        if not results:
            raise HTTPException(status_code=404, detail="Report creation failed")

        row = results[0]
        return {
            "report_id": row[0],
            "report_type": row[1],
            "status": row[2],
            "created_at": row[3],
            "completed_at": None,
            "result_url": None,
            "error_message": None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create report: {str(e)}")


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
        report_id: str,
        current_user=Depends(get_current_active_user),
        ch_client=Depends(get_clickhouse_client)
):
    """
    Get a report by ID
    """
    try:
        query = f"""
        SELECT report_id, report_type, created_by, status, created_at, completed_at, result_url, error_message
        FROM reports
        WHERE report_id = '{report_id}'
        """

        results = ch_client.execute(query)
        if not results:
            raise HTTPException(status_code=404, detail="Report not found")

        row = results[0]

        # Check permissions - only report creator, admins, or instructors for relevant courses can view
        if ("admin" not in [role.name for role in current_user.roles] and
                current_user.id != row[2]):
            # In a real implementation, check if instructor has access to this report
            pass

        return {
            "report_id": row[0],
            "report_type": row[1],
            "status": row[3],
            "created_at": row[4],
            "completed_at": row[5],
            "result_url": row[6],
            "error_message": row[7]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
        report_type: Optional[ReportType] = None,
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
        current_user=Depends(get_current_active_user),
        ch_client=Depends(get_clickhouse_client)
):
    """
    List reports, filtered by type if specified
    """
    try:
        # Build query based on user role
        if "admin" in [role.name for role in current_user.roles]:
            # Admins can see all reports
            base_query = "SELECT report_id, report_type, created_by, status, created_at, completed_at, result_url"
        else:
            # Regular users can only see their own reports
            base_query = f"""
            SELECT report_id, report_type, created_by, status, created_at, completed_at, result_url
            WHERE created_by = {current_user.id}
            """

        # Add type filter if specified
        if report_type:
            if "WHERE" in base_query:
                base_query += f" AND report_type = '{report_type}'"
            else:
                base_query += f" WHERE report_type = '{report_type}'"

        # Complete query with ordering and limits
        query = f"""
        {base_query}
        FROM reports
        ORDER BY created_at DESC
        LIMIT {limit} OFFSET {offset}
        """

        results = ch_client.execute(query)

        reports = []
        for row in results:
            reports.append({
                "report_id": row[0],
                "report_type": row[1],
                "status": row[3],
                "created_at": row[4],
                "completed_at": row[5],
                "result_url": row[6],
                "error_message": None
            })

        return reports

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.delete("/reports/{report_id}", status_code=204)
async def delete_report(
        report_id: str,
        current_user=Depends(get_current_active_user),
        ch_client=Depends(get_clickhouse_client)
):
    """
    Delete a report
    """
    try:
        # Check if report exists and who created it
        query = f"""
        SELECT created_by
        FROM reports
        WHERE report_id = '{report_id}'
        """

        results = ch_client.execute(query)
        if not results:
            raise HTTPException(status_code=404, detail="Report not found")

        created_by = results[0][0]

        # Check permissions - only report creator or admins can delete
        if "admin" not in [role.name for role in current_user.roles] and current_user.id != created_by:
            raise HTTPException(status_code=403, detail="Not authorized to delete this report")

        # Delete the report
        delete_query = f"""
        ALTER TABLE reports
        DELETE WHERE report_id = '{report_id}'
        """

        ch_client.execute(delete_query)

        # Also delete the report file if it exists
        # This would be implemented with your file storage system

        return {}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")