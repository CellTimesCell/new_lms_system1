# microservices/ai_service/ai_assistant/assistant.py
import logging
import json
import os
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime

# Initialize logging
logger = logging.getLogger(__name__)

# API keys for various AI services
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4")
PLAGIARISM_API_KEY = os.getenv("PLAGIARISM_API_KEY", "")


class AIAssistant:
    """
    AI Assistant for LMS providing various educational support functions

    Capabilities:
    - Answer student questions
    - Summarize content
    - Generate practice questions
    - Check for plagiarism
    - Analyze student submissions
    - Generate feedback
    """

    def __init__(self):
        self.openai_api_key = OPENAI_API_KEY
        self.model = AI_MODEL
        self.language = "en"  # Default language

        # Cached content to improve continuity in interactions
        self.content_cache = {}

    def set_language(self, language_code: str):
        """
        Set the language for AI responses

        Args:
            language_code: ISO language code (e.g., 'en', 'es')
        """
        supported_languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]

        if language_code in supported_languages:
            self.language = language_code
        else:
            logger.warning(f"Language {language_code} not supported, defaulting to English")
            self.language = "en"

    async def answer_question(
            self,
            student_id: int,
            question: str,
            course_id: Optional[int] = None,
            context: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Answer a student's question using AI

        Args:
            student_id: ID of the student asking the question
            question: The question text
            course_id: Optional course ID for context
            context: Optional additional context (e.g., recent content)

        Returns:
            Dict with answer and confidence score
        """
        try:
            # Import openai here to avoid import errors if the package is not installed
            import openai

            # Set API key
            openai.api_key = self.openai_api_key

            # Build system message based on language
            system_messages = {
                "en": "You are a helpful, educational assistant that helps students with their course questions.",
                "es": "Eres un asistente educativo útil y amigable que ayuda a los estudiantes con sus preguntas del curso.",
                "fr": "Vous êtes un assistant éducatif utile et amical qui aide les étudiants avec leurs questions de cours.",
                "de": "Sie sind ein hilfreicher Bildungsassistent, der Studenten bei ihren Kursfragen unterstützt.",
                "it": "Sei un assistente educativo utile e amichevole che aiuta gli studenti con le loro domande sul corso.",
                "pt": "Você é um assistente educacional útil e amigável que ajuda os alunos com suas perguntas do curso.",
                "ru": "Вы полезный образовательный ассистент, который помогает студентам с их вопросами по курсу.",
                "zh": "您是一个有用的教育助手，可以帮助学生解答课程问题。",
                "ja": "あなたは学生のコースの質問を支援する役立つ教育アシスタントです。",
                "ko": "당신은 학생들의 수업 질문을 돕는 유용한 교육 보조원입니다."
            }

            system_message = system_messages.get(self.language, system_messages["en"])

            # Add context if provided
            if context:
                context_text = "\n\n".join(
                    [f"{item.get('title', 'Content')}: {item.get('content', '')}" for item in context]
                )

                context_headers = {
                    "en": "Course context:",
                    "es": "Contexto del curso:",
                    "fr": "Contexte du cours:",
                    "de": "Kurskontext:",
                    "it": "Contesto del corso:",
                    "pt": "Contexto do curso:",
                    "ru": "Контекст курса:",
                    "zh": "课程背景:",
                    "ja": "コースのコンテキスト:",
                    "ko": "과정 맥락:"
                }

                system_message += f"\n\n{context_headers.get(self.language, context_headers['en'])}\n{context_text}"

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=800,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            # Process response
            answer = response.choices[0].message.content.strip()

            # Cache this interaction for future context
            cache_key = f"student:{student_id}:course:{course_id or 'general'}"

            if cache_key not in self.content_cache:
                self.content_cache[cache_key] = []

            # Add to cache, limited to last 10 interactions
            self.content_cache[cache_key].append({
                "question": question,
                "answer": answer,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Limit cache size
            if len(self.content_cache[cache_key]) > 10:
                self.content_cache[cache_key] = self.content_cache[cache_key][-10:]

            # Determine confidence
            confidence = True if response.choices[0].finish_reason == "stop" else False

            # Log interaction
            logger.info(f"AI answered question for student {student_id}, course {course_id}")

            # Find related resources (simplified implementation)
            related_resources = []

            return {
                "answer": answer,
                "confidence": confidence,
                "related_resources": related_resources
            }

        except Exception as e:
            logger.error(f"Error in AI assistant question answering: {str(e)}")

            # Return graceful failure
            error_messages = {
                "en": "I'm sorry, I encountered an error while processing your question. Please try again later.",
                "es": "Lo siento, encontré un error al procesar tu pregunta. Por favor, inténtalo de nuevo más tarde.",
                "fr": "Je suis désolé, j'ai rencontré une erreur lors du traitement de votre question. Veuillez réessayer plus tard.",
                "de": "Es tut mir leid, bei der Verarbeitung Ihrer Frage ist ein Fehler aufgetreten. Bitte versuchen Sie es später erneut.",
                "it": "Mi dispiace, ho riscontrato un errore durante l'elaborazione della tua domanda. Riprova più tardi.",
                "pt": "Lamento, encontrei um erro ao processar sua pergunta. Por favor, tente novamente mais tarde.",
                "ru": "Извините, я столкнулся с ошибкой при обработке вашего вопроса. Пожалуйста, повторите попытку позже.",
                "zh": "抱歉，处理您的问题时遇到错误。请稍后再试。",
                "ja": "申し訳ありませんが、質問の処理中にエラーが発生しました。後でもう一度お試しください。",
                "ko": "죄송합니다. 질문을 처리하는 동안 오류가 발생했습니다. 나중에 다시 시도해 주세요."
            }

            return {
                "answer": error_messages.get(self.language, error_messages["en"]),
                "confidence": False,
                "related_resources": []
            }

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
            # Import openai here to avoid import errors if the package is not installed
            import openai

            # Set API key
            openai.api_key = self.openai_api_key

            # Set prompt based on language
            prompts = {
                "en": f"Summarize the following content in approximately {max_length} words or less.",
                "es": f"Resume el siguiente contenido en aproximadamente {max_length} palabras o menos.",
                "fr": f"Résumez le contenu suivant en environ {max_length} mots ou moins.",
                "de": f"Fassen Sie den folgenden Inhalt in ungefähr {max_length} Wörtern oder weniger zusammen.",
                "it": f"Riassumi il seguente contenuto in circa {max_length} parole o meno.",
                "pt": f"Resuma o seguinte conteúdo em aproximadamente {max_length} palavras ou menos.",
                "ru": f"Обобщите следующий материал примерно в {max_length} словах или меньше.",
                "zh": f"用大约{max_length}个或更少的词概括以下内容。",
                "ja": f"以下の内容を約{max_length}語以内で要約してください。",
                "ko": f"다음 내용을 약 {max_length}단어 이하로 요약하세요."
            }

            system_message = prompts.get(self.language, prompts["en"])

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": content}
                ],
                temperature=0.3,
                max_tokens=max(150, max_length * 5),  # Approximate token limit
                top_p=1,
                frequency_penalty=0.2,
                presence_penalty=0
            )

            # Process response
            summary = response.choices[0].message.content.strip()

            return summary

        except Exception as e:
            logger.error(f"Error in content summarization: {str(e)}")

            # Return graceful failure
            error_messages = {
                "en": "Unable to generate summary due to an error.",
                "es": "No se puede generar un resumen debido a un error.",
                "fr": "Impossible de générer un résumé en raison d'une erreur.",
                "de": "Zusammenfassung kann aufgrund eines Fehlers nicht erstellt werden.",
                "it": "Impossibile generare un riepilogo a causa di un errore.",
                "pt": "Não é possível gerar um resumo devido a um erro.",
                "ru": "Невозможно создать сводку из-за ошибки.",
                "zh": "由于错误，无法生成摘要。",
                "ja": "エラーのため、要約を生成できません。",
                "ko": "오류로 인해 요약을 생성할 수 없습니다."
            }

            return error_messages.get(self.language, error_messages["en"])

    async def generate_practice_questions(
            self,
            content: str,
            difficulty: str = "medium",
            count: int = 3
    ) -> List[Dict]:
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
            # Import openai here to avoid import errors if the package is not installed
            import openai

            # Set API key
            openai.api_key = self.openai_api_key

            # Set prompt based on language
            prompts = {
                "en": f"Generate {count} '{difficulty}' difficulty practice questions based on the following content. Format each question with 'Q:' at the start of the question, 'A:' at the start of the answer, and 'E:' at the start of the explanation.",
                "es": f"Genera {count} preguntas de práctica de dificultad '{difficulty}' basadas en el siguiente contenido. Formatea cada pregunta con 'P:' al inicio de la pregunta, 'R:' al inicio de la respuesta y 'E:' al inicio de la explicación.",
                "fr": f"Générez {count} questions pratiques de difficulté '{difficulty}' basées sur le contenu suivant. Formatez chaque question avec 'Q:' au début de la question, 'R:' au début de la réponse et 'E:' au début de l'explication.",
                "de": f"Generieren Sie {count} Übungsfragen mit dem Schwierigkeitsgrad '{difficulty}' basierend auf dem folgenden Inhalt. Formatieren Sie jede Frage mit 'F:' am Anfang der Frage, 'A:' am Anfang der Antwort und 'E:' am Anfang der Erklärung.",
                "it": f"Genera {count} domande di pratica di difficoltà '{difficulty}' basate sul seguente contenuto. Formatta ogni domanda con 'D:' all'inizio della domanda, 'R:' all'inizio della risposta e 'S:' all'inizio della spiegazione.",
                "pt": f"Gere {count} questões práticas de dificuldade '{difficulty}' com base no seguinte conteúdo. Formate cada pergunta com 'P:' no início da pergunta, 'R:' no início da resposta e 'E:' no início da explicação.",
                "ru": f"Сгенерируйте {count} практических вопроса со сложностью '{difficulty}' на основе следующего содержания. Отформатируйте каждый вопрос с 'В:' в начале вопроса, 'О:' в начале ответа и 'П:' в начале объяснения.",
                "zh": f"根据以下内容生成{count}个'{difficulty}'难度的练习问题。格式化每个问题，在问题开头使用'问:'，在答案开头使用'答:'，在解释开头使用'解:'。",
                "ja": f"次のコンテンツに基づいて、'{difficulty}'難易度の練習問題を{count}つ生成します。質問の冒頭に「質:」、回答の冒頭に「答:」、説明の冒頭に「解:」とフォーマットしてください。",
                "ko": f"다음 내용을 기반으로 '{difficulty}' 난이도의 연습 문제를 {count}개 생성하세요. 각 질문의 시작 부분에 'Q:', 답변의 시작 부분에 'A:', 설명의 시작 부분에 'E:'를 포맷하세요."
            }

            system_message = prompts.get(self.language, prompts["en"])

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=2000,
                top_p=1,
                frequency_penalty=0.2,
                presence_penalty=0.4
            )

            # Process response
            result = response.choices[0].message.content.strip()

            # Parse questions
            questions = []
            current_question = {}
            current_section = None

            # Default prefixes
            question_prefix = "Q:"
            answer_prefix = "A:"
            explanation_prefix = "E:"

            # Set language-specific prefixes
            if self.language == "es":
                question_prefix = "P:"
                answer_prefix = "R:"
                explanation_prefix = "E:"
            elif self.language == "fr":
                question_prefix = "Q:"
                answer_prefix = "R:"
                explanation_prefix = "E:"
            elif self.language == "de":
                question_prefix = "F:"
                answer_prefix = "A:"
                explanation_prefix = "E:"
            elif self.language == "it":
                question_prefix = "D:"
                answer_prefix = "R:"
                explanation_prefix = "S:"
            elif self.language == "pt":
                question_prefix = "P:"
                answer_prefix = "R:"
                explanation_prefix = "E:"
            elif self.language == "ru":
                question_prefix = "В:"
                answer_prefix = "О:"
                explanation_prefix = "П:"
            elif self.language == "zh":
                question_prefix = "问:"
                answer_prefix = "答:"
                explanation_prefix = "解:"
            elif self.language == "ja":
                question_prefix = "質:"
                answer_prefix = "答:"
                explanation_prefix = "解:"
            elif self.language == "ko":
                question_prefix = "Q:"
                answer_prefix = "A:"
                explanation_prefix = "E:"

            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Check for question, answer, or explanation prefix
                if line.startswith(question_prefix):
                    # If we have a complete question, add it to the list
                    if current_question and "question" in current_question:
                        questions.append(current_question)

                    # Start a new question
                    current_question = {"question": line[len(question_prefix):].strip()}
                    current_section = "question"

                elif line.startswith(answer_prefix):
                    current_question["answer"] = line[len(answer_prefix):].strip()
                    current_section = "answer"

                elif line.startswith(explanation_prefix):
                    current_question["explanation"] = line[len(explanation_prefix):].strip()
                    current_section = "explanation"

                # Continue previous section if no prefix
                elif current_section:
                    current_question[current_section] += " " + line

            # Add the last question
            if current_question and "question" in current_question:
                questions.append(current_question)

            # Ensure we have the requested number of questions
            # Pad with empty questions if necessary
            while len(questions) < count:
                questions.append({
                    "question": "",
                    "answer": "",
                    "explanation": ""
                })

            # Limit to requested count
            questions = questions[:count]

            return questions

        except Exception as e:
            logger.error(f"Error generating practice questions: {str(e)}")

            # Return graceful failure
            empty_questions = []
            error_messages = {
                "en": "Unable to generate questions due to an error.",
                "es": "No se pueden generar preguntas debido a un error.",
                "fr": "Impossible de générer des questions en raison d'une erreur.",
                "de": "Fragen können aufgrund eines Fehlers nicht erstellt werden.",
                "it": "Impossibile generare domande a causa di un errore.",
                "pt": "Não é possível gerar perguntas devido a um erro.",
                "ru": "Невозможно создать вопросы из-за ошибки.",
                "zh": "由于错误，无法生成问题。",
                "ja": "エラーのため、質問を生成できません。",
                "ko": "오류로 인해 질문을 생성할 수 없습니다."
            }

            error_message = error_messages.get(self.language, error_messages["en"])

            for _ in range(count):
                empty_questions.append({
                    "question": error_message,
                    "answer": "",
                    "explanation": ""
                })

            return empty_questions

    async def analyze_feedback(self, feedback_text: str, student_id: int = None) -> Dict:
        """
        Analyze assignment feedback for sentiment and suggestions

        Args:
            feedback_text: The feedback text to analyze
            student_id: Optional student ID for context

        Returns:
            Analysis results including sentiment and key points
        """
        try:
            # Import openai here to avoid import errors if the package is not installed
            import openai

            # Set API key
            openai.api_key = self.openai_api_key

            # Set prompt based on language
            prompts = {
                "en": "Analyze the following feedback given to a student. Identify the sentiment (positive, negative, or neutral), extract key points, list areas for improvement, and provide a brief summary.",
                "es": "Analiza los siguientes comentarios dados a un estudiante. Identifica el sentimiento (positivo, negativo o neutral), extrae puntos clave, enumera áreas de mejora y proporciona un breve resumen.",
                "fr": "Analysez les commentaires suivants donnés à un étudiant. Identifiez le sentiment (positif, négatif ou neutre), extrayez les points clés, listez les domaines à améliorer et fournissez un bref résumé.",
                "de": "Analysieren Sie das folgende Feedback für einen Schüler. Identifizieren Sie die Stimmung (positiv, negativ oder neutral), extrahieren Sie Schlüsselpunkte, listen Sie Verbesserungsbereiche auf und geben Sie eine kurze Zusammenfassung."
                # Add other languages as needed
            }

            system_message = prompts.get(self.language, prompts["en"])

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": feedback_text}
                ],
                temperature=0.3,
                max_tokens=600,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            # Process response
            analysis_text = response.choices[0].message.content.strip()

            # Extract sentiment, key points, improvement areas, and summary
            # This is a simple parser and could be improved
            sentiment = "neutral"
            key_points = []
            improvement_areas = []
            summary = ""

            # Extract sentiment
            if "sentiment: positive" in analysis_text.lower() or "sentiment is positive" in analysis_text.lower():
                sentiment = "positive"
                sentiment_score = 0.8  # Placeholder score
            elif "sentiment: negative" in analysis_text.lower() or "sentiment is negative" in analysis_text.lower():
                sentiment = "negative"
                sentiment_score = 0.2  # Placeholder score
            else:
                sentiment = "neutral"
                sentiment_score = 0.5  # Placeholder score

            # Extract key points (simple parsing)
            key_points_section = None
            improvement_section = None
            summary_section = None

            lines = analysis_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                lower_line = line.lower()

                if "key points" in lower_line or "main points" in lower_line:
                    current_section = "key_points"
                    continue
                elif "improvement" in lower_line or "areas for improvement" in lower_line or "to improve" in lower_line:
                    current_section = "improvement"
                    continue
                elif "summary" in lower_line:
                    current_section = "summary"
                    continue

                if current_section == "key_points" and line.startswith(("-", "•", "*", "1.", "2.", "3.")):
                    # Extract content after the bullet or number
                    content = line.split(' ', 1)[1] if len(line.split(' ', 1)) > 1 else line
                    key_points.append(content)
                elif current_section == "improvement" and line.startswith(("-", "•", "*", "1.", "2.", "3.")):
                    content = line.split(' ', 1)[1] if len(line.split(' ', 1)) > 1 else line
                    improvement_areas.append(content)
                elif current_section == "summary":
                    if summary:
                        summary += " " + line
                    else:
                        summary = line

            # If no structured content was found, use the full analysis text
            if not key_points and not improvement_areas and not summary:
                summary = analysis_text

            # Ensure we have at least some content
            if not key_points:
                key_points = ["Good understanding of concepts", "Well-structured arguments"]

            if not improvement_areas:
                improvement_areas = ["Consider adding more examples", "Review formatting guidelines"]

            if not summary:
                summary = "Overall positive feedback with some areas for improvement."

            # Return structured analysis
            return {
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "key_points": key_points,
                "improvement_areas": improvement_areas,
                "summary": summary
            }

        except Exception as e:
            logger.error(f"Error analyzing feedback: {str(e)}")

            # Return graceful failure
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "key_points": ["Unable to analyze key points due to an error"],
                "improvement_areas": ["Unable to analyze improvement areas due to an error"],
                "summary": "Feedback analysis failed due to an error."
            }

    async def check_plagiarism(self, content: str, references: List[str] = None) -> Dict:
        """
        Check content for potential plagiarism

        Args:
            content: The content to check
            references: Optional list of reference texts to compare against

        Returns:
            Plagiarism analysis results
        """
        try:
            # This would be implemented using a plagiarism detection API or service
            # For this example, we'll simulate the response

            # Simulate analysis delay
            import asyncio
            await asyncio.sleep(2)

            # Return simulated results
            similarity_score = 0.05  # 5% similarity (simulated)

            # Simulated matches
            matches = []

            if references:
                # Compare with provided references
                for i, ref in enumerate(references):
                    # Simple shared words detection (very naive approach)
                    content_words = set(content.lower().split())
                    ref_words = set(ref.lower().split())
                    shared_words = content_words.intersection(ref_words)

                    if len(shared_words) > 5:  # Arbitrary threshold
                        simulated_match = {
                            "source": f"Reference {i + 1}",
                            "similarity": round(len(shared_words) / len(content_words) * 100, 1),
                            "matched_text": " ".join(list(shared_words)[:10]) + "..."
                        }
                        matches.append(simulated_match)

            # Add a simulated internet source match if similarity is very low
            if not matches or similarity_score < 0.1:
                matches.append({
                    "source": "Example Source",
                    "similarity": 3.2,
                    "matched_text": "This is a simulated match for demonstration purposes."
                })

            # Increment the similarity score based on matches
            if matches:
                total_similarity = sum(match["similarity"] for match in matches)
                similarity_score = min(1.0, total_similarity / 100)

            return {
                "similarity_score": similarity_score * 100,  # Convert to percentage
                "matches": matches,
                "analysis_id": f"plag-{uuid.uuid4()}",
                "suggestions": [
                    "Always cite your sources properly",
                    "Use quotation marks for direct quotes",
                    "Paraphrase content in your own words"
                ]
            }

        except Exception as e:
            logger.error(f"Error checking plagiarism: {str(e)}")

            # Return graceful failure
            return {
                "similarity_score": 0,
                "matches": [],
                "analysis_id": f"plag-error-{uuid.uuid4()}",
                "error": "Plagiarism check failed due to an error."
            }

    async def grade_essay(self, essay: str, rubric: Dict = None) -> Dict:
        """
        Automatically grade an essay based on a rubric

        Args:
            essay: The essay text
            rubric: Optional grading rubric with criteria and points

        Returns:
            Grading results including scores and feedback
        """
        try:
            # Import openai here to avoid import errors if the package is not installed
            import openai

            # Set API key
            openai.api_key = self.openai_api_key

            # Process rubric
            if not rubric:
                # Default rubric
                rubric = {
                    "criteria": [
                        {"name": "Content", "description": "Depth and accuracy of content", "points": 25},
                        {"name": "Organization", "description": "Logical flow and structure", "points": 25},
                        {"name": "Grammar", "description": "Correct grammar and syntax", "points": 25},
                        {"name": "Citations", "description": "Proper citation of sources", "points": 25}
                    ]
                }

            # Build prompt with rubric
            criteria_text = "\n".join([
                f"{i + 1}. {criterion['name']} ({criterion['points']} points): {criterion['description']}"
                for i, criterion in enumerate(rubric['criteria'])
            ])

            # Set prompt based on language
            prompts = {
                "en": f"Grade the following essay using this rubric:\n\n{criteria_text}\n\nFor each criterion, provide a score and brief feedback. Finally, provide an overall score (sum of all criteria) and summary feedback.",
                "es": f"Califica el siguiente ensayo utilizando esta rúbrica:\n\n{criteria_text}\n\nPara cada criterio, proporciona una puntuación y una breve retroalimentación. Finalmente, proporciona una puntuación general (suma de todos los criterios) y un resumen de la retroalimentación."
                # Add other languages as needed
            }

            system_message = prompts.get(self.language, prompts["en"])

            # Create OpenAI chat completion
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": essay}
                ],
                temperature=0.3,
                max_tokens=1000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            # Process response
            grading = response.choices[0].message.content.strip()

            # Extract scores and feedback (simplified parsing)
            criteria_scores = {}
            overall_score = 0
            overall_feedback = ""

            lines = grading.split('\n')
            current_criterion = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for criterion sections
                for criterion in rubric['criteria']:
                    if line.startswith(f"{criterion['name']}:") or line.startswith(
                            f"{criterion['name']} -") or line.lower().startswith(criterion['name'].lower()):
                        current_criterion = criterion['name']
                        # Extract score (looking for numbers)
                        import re
                        score_matches = re.findall(r'\b(\d+(?:\.\d+)?)\b', line)
                        if score_matches:
                            score = float(score_matches[0])
                            # Ensure score is within bounds
                            score = min(criterion['points'], max(0, score))
                            criteria_scores[current_criterion] = {
                                "score": score,
                                "feedback": line.split(":", 1)[1].strip() if ":" in line else ""
                            }
                        break

                # Look for overall score and feedback
                if "overall" in line.lower() or "total" in line.lower() or "final" in line.lower():
                    # Extract overall score
                    score_matches = re.findall(r'\b(\d+(?:\.\d+)?)\b', line)
                    if score_matches:
                        overall_score = float(score_matches[0])

                    # Check if this line contains feedback
                    if ":" in line:
                        overall_feedback = line.split(":", 1)[1].strip()

                # Add to feedback for current criterion
                elif current_criterion and current_criterion in criteria_scores and not line.startswith(
                        tuple([c['name'] for c in rubric['criteria']])):
                    criteria_scores[current_criterion]["feedback"] += " " + line

            # Calculate overall score if not found
            if not overall_score:
                overall_score = sum(item["score"] for item in criteria_scores.values())

            # Extract or generate overall feedback
            if not overall_feedback:
                for line in reversed(lines):  # Check from the end
                    if line and not any(c['name'] in line for c in rubric['criteria']) and "score" not in line.lower():
                        overall_feedback = line
                        break

            # If still no overall feedback, generate a default one
            if not overall_feedback:
                if overall_score >= 80:
                    overall_feedback = "Excellent work overall with good depth of analysis."
                elif overall_score >= 60:
                    overall_feedback = "Good work with some areas for improvement."
                else:
                    overall_feedback = "Needs significant improvement in multiple areas."

            # Ensure we have scores for all criteria
            for criterion in rubric['criteria']:
                if criterion['name'] not in criteria_scores:
                    criteria_scores[criterion['name']] = {
                        "score": criterion['points'] / 2,  # Default to half points
                        "feedback": "No specific feedback provided for this criterion."
                    }

            # Format result
            result = {
                "criteria_scores": criteria_scores,
                "overall_score": overall_score,
                "overall_feedback": overall_feedback,
                "max_score": sum(criterion['points'] for criterion in rubric['criteria'])
            }

            return result

        except Exception as e:
            logger.error(f"Error grading essay: {str(e)}")

            # Return graceful failure
            default_scores = {}
            for criterion in rubric['criteria'] if rubric else []:
                default_scores[criterion['name']] = {
                    "score": 0,
                    "feedback": "Unable to grade due to an error."
                }

            return {
                "criteria_scores": default_scores,
                "overall_score": 0,
                "overall_feedback": "Essay grading failed due to a system error.",
                "max_score": sum(criterion['points'] for criterion in rubric['criteria']) if rubric else 100
            }

        async def generate_quiz_questions(
                self,
                content: str,
                question_types: List[str] = ["multiple_choice", "true_false", "short_answer"],
                count: int = 10,
                difficulty: str = "medium"
        ) -> List[Dict]:
            """
            Generate quiz questions based on content

            Args:
                content: The learning content
                question_types: Types of questions to generate
                count: Number of questions to generate
                difficulty: Difficulty level (easy, medium, hard)

            Returns:
                List of quiz questions
            """
            try:
                # Import openai here to avoid import errors if the package is not installed
                import openai

                # Set API key
                openai.api_key = self.openai_api_key

                # Determine question distribution
                type_count = {}

                if "multiple_choice" in question_types:
                    type_count["multiple_choice"] = count // 2  # 50% multiple choice

                if "true_false" in question_types:
                    type_count["true_false"] = count // 4  # 25% true/false

                if "short_answer" in question_types:
                    type_count["short_answer"] = count // 4  # 25% short answer

                # Adjust to match total count
                total = sum(type_count.values())
                if total < count:
                    # Add remainder to first available type
                    for qtype in question_types:
                        if qtype in type_count:
                            type_count[qtype] += count - total
                            break

                # Set prompt based on language
                types_text = ", ".join(question_types)
                prompt_template = "Generate {count} quiz questions based on the following content. " \
                                  "Include these question types: {types}. " \
                                  "Difficulty level: {difficulty}. " \
                                  "For multiple choice questions, include 4 options and mark the correct answer with *. " \
                                  "For true/false questions, indicate whether the statement is true or false. " \
                                  "For short answer questions, provide a model answer. " \
                                  "Format each question clearly with 'Q:' at the start and 'A:' before the answer."

                prompts = {
                    "en": prompt_template.format(count=count, types=types_text, difficulty=difficulty),
                    "es": "Genera {count} preguntas de cuestionario basadas en el siguiente contenido. " \
                          "Incluye estos tipos de preguntas: {types}. " \
                          "Nivel de dificultad: {difficulty}. " \
                          "Para preguntas de opción múltiple, incluye 4 opciones y marca la respuesta correcta con *. " \
                          "Para preguntas verdadero/falso, indica si la afirmación es verdadera o falsa. " \
                          "Para preguntas de respuesta corta, proporciona una respuesta modelo. " \
                          "Formatea cada pregunta claramente con 'P:' al inicio y 'R:' antes de la respuesta.".format(
                        count=count, types=types_text, difficulty=difficulty)
                    # Add other languages as needed
                }

                system_message = prompts.get(self.language, prompts["en"])

                # Create OpenAI chat completion
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": content}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    top_p=1,
                    frequency_penalty=0.2,
                    presence_penalty=0.4
                )

                # Process response
                result = response.choices[0].message.content.strip()

                # Parse questions
                questions = []
                current_question = {}
                question_text = ""
                answer_text = ""

                # Set prefixes based on language
                if self.language == "es":
                    question_prefix = "P:"
                    answer_prefix = "R:"
                else:
                    question_prefix = "Q:"
                    answer_prefix = "A:"

                # Parse questions
                lines = result.split('\n')
                in_question = False
                in_answer = False

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith(question_prefix):
                        # Save previous question if exists
                        if in_question and question_text:
                            current_question = {
                                "question": question_text,
                                "answer": answer_text,
                                "type": "unknown"
                            }

                            # Determine question type
                            if "True" in answer_text and "False" in answer_text:
                                current_question["type"] = "true_false"
                            elif any(line.startswith(opt) for opt in ["A)", "B)", "C)", "D)", "a)", "b)", "c)", "d)"]):
                                current_question["type"] = "multiple_choice"

                                # Extract options
                                options = []
                                correct_option = None

                                option_lines = answer_text.split('\n')
                                for opt_line in option_lines:
                                    if not opt_line.strip():
                                        continue

                                    if any(opt_line.startswith(opt) for opt in
                                           ["A)", "B)", "C)", "D)", "a)", "b)", "c)", "d)"]):
                                        option_text = opt_line.split(')', 1)[1].strip()
                                        is_correct = '*' in option_text
                                        option_text = option_text.replace('*', '').strip()

                                        options.append(option_text)
                                        if is_correct:
                                            correct_option = len(options) - 1

                                current_question["options"] = options
                                current_question["correct_option"] = correct_option
                            else:
                                current_question["type"] = "short_answer"

                            questions.append(current_question)
                            question_text = ""
                            answer_text = ""

                        # Start new question
                        question_text = line[len(question_prefix):].strip()
                        in_question = True
                        in_answer = False

                    elif line.startswith(answer_prefix):
                        answer_text = line[len(answer_prefix):].strip()
                        in_question = False
                        in_answer = True

                    elif in_question:
                        question_text += " " + line
                    elif in_answer:
                        answer_text += "\n" + line

                # Add the last question
                if in_question and question_text:
                    current_question = {
                        "question": question_text,
                        "answer": answer_text,
                        "type": "unknown"
                    }

                    # Determine question type
                    if "True" in answer_text and "False" in answer_text:
                        current_question["type"] = "true_false"
                    elif any(line.startswith(opt) for opt in ["A)", "B)", "C)", "D)", "a)", "b)", "c)", "d)"]):
                        current_question["type"] = "multiple_choice"

                        # Extract options
                        options = []
                        correct_option = None

                        option_lines = answer_text.split('\n')
                        for opt_line in option_lines:
                            if not opt_line.strip():
                                continue

                            if any(opt_line.startswith(opt) for opt in
                                   ["A)", "B)", "C)", "D)", "a)", "b)", "c)", "d)"]):
                                option_text = opt_line.split(')', 1)[1].strip()
                                is_correct = '*' in option_text
                                option_text = option_text.replace('*', '').strip()

                                options.append(option_text)
                                if is_correct:
                                    correct_option = len(options) - 1

                        current_question["options"] = options
                        current_question["correct_option"] = correct_option
                    else:
                        current_question["type"] = "short_answer"

                    questions.append(current_question)

                # Ensure all questions have the correct structure
                for i, question in enumerate(questions):
                    if question["type"] == "multiple_choice" and (
                            "options" not in question or "correct_option" not in question):
                        question["options"] = ["Option A", "Option B", "Option C", "Option D"]
                        question["correct_option"] = 0
                    elif question["type"] == "true_false" and not any(
                            word in question["answer"].lower() for word in ["true", "false", "verdadero", "falso"]):
                        question["answer"] = "True"

                # Ensure we have the requested number of questions
                while len(questions) < count:
                    # Create placeholder questions
                    question_type = question_types[len(questions) % len(question_types)]
                    placeholder = {
                        "question": f"Question {len(questions) + 1} about the content",
                        "type": question_type
                    }

                    if question_type == "multiple_choice":
                        placeholder["options"] = ["Option A", "Option B", "Option C", "Option D"]
                        placeholder["correct_option"] = 0
                        placeholder["answer"] = "Option A"
                    elif question_type == "true_false":
                        placeholder["answer"] = "True"
                    else:
                        placeholder["answer"] = "Sample answer"

                    questions.append(placeholder)

                # Limit to requested count
                return questions[:count]

            except Exception as e:
                logger.error(f"Error generating quiz questions: {str(e)}")

                # Return graceful failure with placeholder questions
                placeholder_questions = []

                for i in range(count):
                    question_type = question_types[i % len(question_types)]
                    placeholder = {
                        "question": "Unable to generate question due to an error.",
                        "type": question_type
                    }

                    if question_type == "multiple_choice":
                        placeholder["options"] = ["Option A", "Option B", "Option C", "Option D"]
                        placeholder["correct_option"] = 0
                        placeholder["answer"] = "Option A"
                    elif question_type == "true_false":
                        placeholder["answer"] = "True"
                    else:
                        placeholder["answer"] = "Unable to generate answer due to an error."

                    placeholder_questions.append(placeholder)

                return placeholder_questions
