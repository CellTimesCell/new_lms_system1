# microservices/ai_service/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class QuestionRequest(BaseModel):
    """Schema for question answering request"""
    question: str
    course_id: Optional[int] = None
    context: Optional[List[Dict[str, Any]]] = None


class AnswerResponse(BaseModel):
    """Schema for question answering response"""
    question: str
    answer: str
    confidence: bool
    related_resources: List[Dict[str, Any]] = []


class ContentSummaryRequest(BaseModel):
    """Schema for content summarization request"""
    content: str
    max_length: int = 200


class SummaryResponse(BaseModel):
    """Schema for content summarization response"""
    original_length: int
    summary_length: int
    summary: str


class Difficulty(str, Enum):
    """Difficulty levels for practice questions"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PracticeQuestionsRequest(BaseModel):
    """Schema for practice questions request"""
    content: str
    difficulty: Difficulty = Difficulty.MEDIUM
    count: int = 3


class PracticeQuestion(BaseModel):
    """Schema for a practice question"""
    question: str
    answer: str
    explanation: Optional[str] = None


class PracticeQuestionsResponse(BaseModel):
    """Schema for practice questions response"""
    questions: List[PracticeQuestion]
    content_hash: int
    difficulty: Difficulty


class FeedbackAnalysisRequest(BaseModel):
    """Schema for feedback analysis request"""
    student_id: int
    assignment_id: int
    submission_id: int
    feedback_text: str


class FeedbackAnalysis(BaseModel):
    """Schema for feedback analysis results"""
    sentiment: str
    sentiment_score: float
    key_points: List[str]
    improvement_areas: List[str]
    summary: str


class FeedbackAnalysisResponse(BaseModel):
    """Schema for feedback analysis response"""
    student_id: int
    assignment_id: int
    submission_id: int
    analysis: FeedbackAnalysis


class PlagiarismCheckRequest(BaseModel):
    """Schema for plagiarism check request"""
    submission_id: int
    content: str
    check_external_sources: bool = True
    check_internal_submissions: bool = True


class PlagiarismMatch(BaseModel):
    """Schema for a plagiarism match"""
    source: str
    similarity: float
    matched_text: str


class PlagiarismCheckResponse(BaseModel):
    """Schema for plagiarism check response"""
    check_id: str
    submission_id: int
    status: str
    similarity_score: Optional[float] = None
    matches: Optional[List[PlagiarismMatch]] = None
    report_url: Optional[str] = None
    message: Optional[str] = None