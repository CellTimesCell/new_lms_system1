# core/lms_core/main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
from typing import List, Dict
import json
import time
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Import routers
from core.lms_core.auth.router import router as auth_router
from core.lms_core.users.router import router as users_router
from core.lms_core.courses.router import router as courses_router
from core.lms_core.assignments.router import router as assignments_router
from core.lms_core.grading.router import router as grading_router
from core.lms_core.auth.validate import router as validate_router

# Setup logging
logging.basicConfig(
    level=logging.INFO if os.getenv("LOG_LEVEL") != "DEBUG" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("lms_core")

# Create the FastAPI application
app = FastAPI(
    title="Learning Management System API",
    description="API for the LMS system",
    version="1.0.0",
)

# Configure CORS - get allowed origins from environment variable
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header with request processing time"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()

    # Get client IP
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0] if forwarded else request.client.host

    # Log request
    logger.info(f"Request: {request.method} {request.url.path} from {ip}")

    # Process request
    response = await call_next(request)

    # Log response time and status code
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} in {process_time:.4f}s")

    return response


# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(courses_router, prefix="/api/v1/courses", tags=["Courses"])
app.include_router(assignments_router, prefix="/api/v1/assignments", tags=["Assignments"])
app.include_router(grading_router, prefix="/api/v1/grading", tags=["Grading"])


# Root endpoint
@app.get("/")
async def root():
    """API root endpoint with basic info"""
    return {
        "name": "Learning Management System API",
        "documentation": "/docs",
        "version": "1.0.0",
        "server_time": datetime.utcnow().isoformat()
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "lms-core-api",
        "timestamp": datetime.utcnow().isoformat()
    }


# Custom exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred",
            "status_code": 500
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Starting LMS Core API")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Shutting down LMS Core API")


# Run the application if executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)