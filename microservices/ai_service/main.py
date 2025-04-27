# microservices/ai_service/main.py
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import List, Dict, Optional
import os
import json
from datetime import datetime

from microservices.ai_service.ai_assistant.assistant import AIAssistant
from microservices.ai_service.schemas import (
    QuestionRequest,
    AnswerResponse,
    ContentSummaryRequest,
    SummaryResponse,
    PracticeQuestionsRequest,
    PracticeQuestionsResponse,
    FeedbackAnalysisRequest,
    FeedbackAnalysisResponse,
    PlagiarismCheckRequest,
    PlagiarismCheckResponse
)
from security.authentication.auth import get_current_active_user

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Assistant Service",
    description="AI-enhanced features for the LMS",
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

# Create AI assistant instance
ai_assistant = AIAssistant()


@app.post("/ai/question", response_model=AnswerResponse)
async def answer_question(
        request: QuestionRequest,
        current_user=Depends(get_current_active_user)
):
    """
    Answer a student's question using AI
    """
    try:
        # Set language based on user preference
        ai_assistant.set_language(current_user.preferred_language)

        # Answer the question
        answer = await ai_assistant.answer_question(
            student_id=current_user.id,
            question=request.question,
            course_id=request.course_id,
            context=request.context
        )

        return {
            "question": request.question,
            "answer": answer["answer"],
            "confidence": answer["confidence"],
            "related_resources": []  # Could be enhanced in the future
        }

    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process question")


@app.post("/ai/summarize", response_model=SummaryResponse)
async def summarize_content(
        request: ContentSummaryRequest,
        current_user=Depends(get_current_active_user)
):
    """
    Summarize content to a specified maximum length
    """
    try:
        # Set language based on user preference
        ai_assistant.set_language(current_user.preferred_language)

        # Summarize the content
        summary = await ai_assistant.summarize_content(
            content=request.content,
            max_length=request.max_length
        )

        return {
            "original_length": len(request.content.split()),
            "summary_length": len(summary.split()),
            "summary": summary
        }

    except Exception as e:
        logger.error(f"Error summarizing content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to summarize content")


@app.post("/ai/practice-questions", response_model=PracticeQuestionsResponse)
async def generate_practice_questions(
        request: PracticeQuestionsRequest,
        current_user=Depends(get_current_active_user)
):
    """
    Generate practice questions based on content
    """
    try:
        # Set language based on user preference
        ai_assistant.set_language(current_user.preferred_language)

        # Generate practice questions
        questions = await ai_assistant.generate_practice_questions(
            content=request.content,
            difficulty=request.difficulty,
            count=request.count
        )

        return {
            "questions": questions,
            "content_hash": hash(request.content) & 0xffffffff,  # Simple content hash for caching
            "difficulty": request.difficulty
        }

    except Exception as e:
        logger.error(f"Error generating practice questions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate practice questions")


@app.post("/ai/feedback-analysis", response_model=FeedbackAnalysisResponse)
async def analyze_feedback(
        request: FeedbackAnalysisRequest,
        current_user=Depends(get_current_active_user)
):
    """
    Analyze submission feedback for sentiment and suggestions
    """
    try:
        # Only instructors and students can access their own feedback
        if "instructor" not in [role.name for role in current_user.roles] and current_user.id != request.student_id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to analyze this feedback"
            )

        # Set language based on user preference
        ai_assistant.set_language(current_user.preferred_language)

        # Analyze the feedback
        # This is a placeholder - you would implement the analysis method in the AIAssistant class
        analysis = {
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "key_points": [
                "Good understanding of core concepts",
                "Well-structured arguments",
                "Needs improvement in citation formatting"
            ],
            "improvement_areas": [
                "Citation formatting",
                "More detailed examples needed"
            ],
            "summary": "Overall positive feedback with minor improvement suggestions."
        }

        return {
            "student_id": request.student_id,
            "assignment_id": request.assignment_id,
            "submission_id": request.submission_id,
            "analysis": analysis
        }

    except Exception as e:
        logger.error(f"Error analyzing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze feedback")


@app.post("/ai/plagiarism-check", response_model=PlagiarismCheckResponse)
async def check_plagiarism(
        request: PlagiarismCheckRequest,
        background_tasks: BackgroundTasks,
        current_user=Depends(get_current_active_user)
):
    """
    Check submission for plagiarism
    """
    try:
        # Only instructors can initiate plagiarism checks
        if "instructor" not in [role.name for role in current_user.roles] and "admin" not in [role.name for role in
                                                                                              current_user.roles]:
            raise HTTPException(
                status_code=403,
                detail="Only instructors can perform plagiarism checks"
            )

        # Generate a check ID
        check_id = f"plag-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hash(request.content) % 1000:03d}"

        # In a real implementation, you would perform the check in the background
        # For this example, we'll just return a placeholder response
        background_tasks.add_task(
            process_plagiarism_check,
            check_id,
            request.content,
            request.submission_id
        )

        return {
            "check_id": check_id,
            "submission_id": request.submission_id,
            "status": "processing",
            "message": "Plagiarism check initiated. Results will be available shortly."
        }

    except Exception as e:
        logger.error(f"Error initiating plagiarism check: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate plagiarism check")


@app.get("/ai/plagiarism-check/{check_id}", response_model=PlagiarismCheckResponse)
async def get_plagiarism_check_result(
        check_id: str,
        current_user=Depends(get_current_active_user)
):
    """
    Get the result of a plagiarism check
    """
    try:
        # Only instructors can view plagiarism check results
        if "instructor" not in [role.name for role in current_user.roles] and "admin" not in [role.name for role in
                                                                                              current_user.roles]:
            raise HTTPException(
                status_code=403,
                detail="Only instructors can view plagiarism check results"
            )

        # In a real implementation, you would retrieve the results from a database
        # For this example, we'll just return a placeholder response
        if not check_id.startswith("plag-"):
            raise HTTPException(status_code=404, detail="Check ID not found")

        # Simulate completed check
        return {
            "check_id": check_id,
            "submission_id": int(check_id.split("-")[2]),
            "status": "completed",
            "similarity_score": 12.5,
            "matches": [
                {
                    "source": "Example Source 1",
                    "similarity": 8.2,
                    "matched_text": "This is an example of matched text from Source 1"
                },
                {
                    "source": "Example Source 2",
                    "similarity": 4.3,
                    "matched_text": "Another example of matched text from Source 2"
                }
            ],
            "report_url": f"/api/ai/plagiarism-reports/{check_id}"
        }

    except Exception as e:
        logger.error(f"Error retrieving plagiarism check: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plagiarism check")


async def process_plagiarism_check(check_id: str, content: str, submission_id: int):
    """
    Process a plagiarism check in the background

    Args:
        check_id: Check ID
        content: Content to check
        submission_id: Submission ID
    """
    # In a real implementation, this would:
    # 1. Break content into chunks
    # 2. Compare against a database of known sources
    # 3. Calculate similarity scores
    # 4. Generate a report
    # 5. Store the results in a database

    logger.info(f"Processing plagiarism check {check_id} for submission {submission_id}")

    # Simulate processing time
    import asyncio
    await asyncio.sleep(5)

    logger.info(f"Completed plagiarism check {check_id}")


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("Starting AI Assistant Service")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown tasks"""
    logger.info("Shutting down AI Assistant Service")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)