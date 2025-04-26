# Content Service for file storage and management
from fastapi import FastAPI, UploadFile, File as FastAPIFile, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
import logging
import os
import shutil
from typing import List, Optional
from uuid import uuid4
from datetime import datetime

from sqlalchemy.orm import Session
from infrastructure.databases.database_config import get_db
from core.lms_core.auth.auth import get_current_active_user
from microservices.content_service.models import File
from microservices.content_service.schemas import FileCreate, FileResponse

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Content Service",
    description="File storage and management service for LMS",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure storage settings
STORAGE_PATH = os.getenv("STORAGE_PATH", "./storage")
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")  # local or s3

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_PATH, exist_ok=True)


@app.post("/files/upload", response_model=FileResponse)
async def upload_file(
        file: UploadFile = FastAPIFile(...),
        description: Optional[str] = Form(None),
        course_id: Optional[int] = Form(None),
        module_id: Optional[int] = Form(None),
        assignment_id: Optional[int] = Form(None),
        submission_id: Optional[int] = Form(None),
        is_public: bool = Form(False),
        current_user=Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Upload a file to the storage system
    """
    try:
        # Generate a unique filename
        original_filename = file.filename
        unique_filename = File.generate_filename(original_filename)

        # Determine file path
        file_path = os.path.join(STORAGE_PATH, unique_filename)

        # Get file content type
        content_type = file.content_type or "application/octet-stream"

        # Determine file type (extension)
        file_type = os.path.splitext(original_filename)[1].lower()[1:]
        if not file_type:
            file_type = "bin"

        # Save file to storage
        if STORAGE_TYPE == "local":
            # Save locally
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        else:
            # S3 implementation would go here
            # This is a placeholder
            file_path = f"s3://bucket/{unique_filename}"

        # Get file size
        file_size = os.path.getsize(file_path) if STORAGE_TYPE == "local" else 0

        # Create file record in database
        db_file = File(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            content_type=content_type,
            uploaded_by_id=current_user.id,
            course_id=course_id,
            module_id=module_id,
            assignment_id=assignment_id,
            submission_id=submission_id,
            is_public=is_public,
            description=description
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return {
            "id": db_file.id,
            "filename": db_file.filename,
            "original_filename": db_file.original_filename,
            "file_size": db_file.file_size,
            "file_type": db_file.file_type,
            "content_type": db_file.content_type,
            "created_at": db_file.created_at,
            "url": f"/api/files/download/{db_file.id}"
        }

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@app.get("/files/download/{file_id}")
async def download_file(
        file_id: int,
        current_user=Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Download a file from the storage system
    """
    # Get file from database
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check permissions
    if not db_file.is_public and db_file.uploaded_by_id != current_user.id:
        # Additional permission checks would go here
        # For example, check if user is instructor for course, etc.
        # For now, just check if user is admin
        user_roles = [role.name for role in current_user.roles]
        if "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this file"
            )

    # Serve file
    if STORAGE_TYPE == "local":
        if not os.path.exists(db_file.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in storage"
            )

        return FileResponse(
            db_file.file_path,
            filename=db_file.original_filename,
            media_type=db_file.content_type
        )
    else:
        # S3 implementation would go here
        # This is a placeholder
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="S3 storage not implemented yet"
        )


@app.get("/files", response_model=List[FileResponse])
async def list_files(
        course_id: Optional[int] = None,
        module_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        current_user=Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    List files with optional filtering
    """
    query = db.query(File)

    # Apply filters
    if course_id:
        query = query.filter(File.course_id == course_id)
    if module_id:
        query = query.filter(File.module_id == module_id)
    if assignment_id:
        query = query.filter(File.assignment_id == assignment_id)

    # Check permissions
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and "instructor" not in user_roles:
        # Students can only see public files or their own
        query = query.filter((File.is_public == True) | (File.uploaded_by_id == current_user.id))

    # Execute query
    files = query.all()

    # Format response
    result = []
    for file in files:
        result.append({
            "id": file.id,
            "filename": file.filename,
            "original_filename": file.original_filename,
            "file_size": file.file_size,
            "file_type": file.file_type,
            "content_type": file.content_type,
            "created_at": file.created_at,
            "url": f"/api/files/download/{file.id}"
        })

    return result


@app.delete("/files/{file_id}")
async def delete_file(
        file_id: int,
        current_user=Depends(get_current_active_user),
        db: Session = Depends(get_db)
):
    """
    Delete a file
    """
    # Get file from database
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    # Check permissions
    if db_file.uploaded_by_id != current_user.id:
        user_roles = [role.name for role in current_user.roles]
        if "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this file"
            )

    # Delete file from storage
    if STORAGE_TYPE == "local":
        if os.path.exists(db_file.file_path):
            os.remove(db_file.file_path)
    else:
        # S3 implementation would go here
        pass

    # Delete file record from database
    db.delete(db_file)
    db.commit()

    return {"message": "File deleted successfully"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)