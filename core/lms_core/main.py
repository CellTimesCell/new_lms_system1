# core/lms_core/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
from typing import List, Dict

from core.lms_core.auth.router import router as auth_router
from core.lms_core.users.router import router as users_router
from core.lms_core.courses.router import router as courses_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(
    title="Learning Management System API",
    description="API for the LMS system",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(courses_router, prefix="/api/v1/courses", tags=["Courses"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Learning Management System API is running",
        "documentation": "/docs",
        "version": "1.0.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "lms-core-api"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting LMS Core API")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down LMS Core API")

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)