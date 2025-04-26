# AI Assistant module for LMS
import logging
import json
import os
from typing import Dict, List, Optional
import openai
from fastapi import FastAPI, HTTPException, BackgroundTasks

# Initialize logging
logger = logging.getLogger(__name__)

# OpenAI client setup
openai.api_key = os.getenv("OPENAI_API_KEY")


class AIAssistant:
    """
    AI Assistant class providing LMS-specific AI functions

    This class provides methods for:
    - Student assistance with course content
    - Assignment help
    - Content summarization
    - Question answering
    """

    def __init__(self):
        self.model = os.getenv("AI_MODEL", "gpt-4")
        self.language = "en"  # Default to English

    def set_language(self, language_code: str):
        """
        Set the language for AI responses

        Args:
            language_code: ISO language code (e.g., 'en', 'es')
        """
        supported_languages = ["en", "es"]
        if language_code in supported_languages:
            self.language = language_code
        else:
            logger.warning(f"Language {language_code} not supported, defaulting to English")
            self.language = "en"

    async def answer_question(self,
                              student_id: int,
                              question: str,
                              course_id: Optional[int] = None,
                              context: Optional[List[Dict]] = None) -> Dict:
        """
        Answer a student's question using AI

        Args:
            student_id: ID of the student asking the question
            question: The question text
            course_id: Optional course ID for context
            context: Optional additional context (e.g., recent content)

        Returns:
            Dictionary with answer and confidence score
        """
        try:
            # Build prompt based on language
            if self.language == "es":
                system_message = "Eres un asistente educativo útil y amigable que ayuda a los estudiantes con sus preguntas del curso."
            else:  # English default
                system_message = "You are a helpful, educational assistant that helps students with their course questions."

            # Add context if provided
            if context:
                context_text = "\n\n".join(
                    [f"{item.get('title', 'Content')}: {item.get('content', '')}" for item in context])
                if self.language == "es":
                    system_message += f"\n\nContexto del curso:\n{context_text}"
                else:
                    system_message += f"\n\nCourse context:\n{context_text}"

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # Process response
            answer = response.choices[0].message.content.strip()

            # Log interaction
            logger.info(f"AI answered question for student {student_id}, course {course_id}")

            return {
                "answer": answer,
                "confidence": response.choices[0].finish_reason == "stop"
            }

        except Exception as e:
            logger.error(f"Error in AI assistant: {str(e)}")
            raise

    async def summarize_content(self, content: str, max_length: int = 200) -> str:
        """
        Summarize content to a specified maximum length

        Args:
            content: The content to summarize
            max_length: Maximum length of summary in words

        Returns:
            Summarized content
        """
        try:
            # Build prompt based on language
            if self.language == "es":
                system_message = f"Resume el siguiente contenido en aproximadamente {max_length} palabras o menos."
            else:  # English default
                system_message = f"Summarize the following content in approximately {max_length} words or less."

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=max(100, max_length * 5)  # Approximate token limit
            )

            # Process response
            summary = response.choices[0].message.content.strip()

            return summary

        except Exception as e:
            logger.error(f"Error in content summarization: {str(e)}")
            raise

    async def generate_practice_questions(self,
                                          content: str,
                                          difficulty: str = "medium",
                                          count: int = 3) -> List[Dict]:
        """
        Generate practice questions based on content

        Args:
            content: The learning content
            difficulty: Difficulty level (easy, medium, hard)
            count: Number of questions to generate

        Returns:
            List of question dictionaries with question, answer, and explanation
        """
        try:
            # Build prompt based on language
            if self.language == "es":
                system_message = f"Genera {count} preguntas de práctica de dificultad '{difficulty}' basadas en el siguiente contenido. Incluye la pregunta, respuesta y una breve explicación para cada una."
            else:  # English default
                system_message = f"Generate {count} '{difficulty}' difficulty practice questions based on the following content. Include the question, answer, and a brief explanation for each."

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            # Process response - in production this would have more robust parsing
            result = response.choices[0].message.content.strip()

            # Simple parsing of questions - would be more robust in production
            questions = []
            current_question = {}

            for line in result.split("\n"):
                line = line.strip()
                if not line:
                    continue

                if line.startswith(("Question", "Pregunta")):
                    if current_question and "question" in current_question:
                        questions.append(current_question)
                    current_question = {"question": line.split(":", 1)[1].strip() if ":" in line else line}
                elif line.startswith(("Answer", "Respuesta")) and current_question:
                    current_question["answer"] = line.split(":", 1)[1].strip() if ":" in line else line
                elif line.startswith(("Explanation", "Explicación")) and current_question:
                    current_question["explanation"] = line.split(":", 1)[1].strip() if ":" in line else line

            # Add the last question
            if current_question and "question" in current_question:
                questions.append(current_question)

            return questions

        except Exception as e:
            logger.error(f"Error generating practice questions: {str(e)}")
            raise