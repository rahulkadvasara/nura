"""
Nura - Conversation Intelligence Service
Uses AI to compile suggested follow-up questions, summaries, titles, and tags
"""

import json
import logging
from typing import Dict, Any, List
from app.services.groq_service import GroqService
from app.repositories.chat_session_repository import ChatSessionRepository
from app.models.chat import ChatSessionUpdate

logger = logging.getLogger(__name__)


class ConversationIntelligenceService:
    """Computes suggested follow-ups, auto-generates chat titles, and scores quality"""

    def __init__(self, groq_service: GroqService, chat_session_repository: ChatSessionRepository):
        self.groq_service = groq_service
        self.chat_session_repository = chat_session_repository

    async def generate_intelligence(
        self,
        user_message: str,
        assistant_response: str
    ) -> Dict[str, Any]:
        """
        Uses Groq LLM to generate suggested follow-ups, conversation title, quality score, and tags
        in a single lightweight JSON response.
        """
        prompt = (
            f"Given the user query: \"{user_message}\"\n"
            f"And the assistant response: \"{assistant_response}\"\n\n"
            "Please generate:\n"
            "1. 3 relevant, highly helpful follow-up questions a patient might ask next (e.g. about medication safety, appointments, symptom checks).\n"
            "2. A short title (3-5 words) summarizing this session's topic.\n"
            "3. 2-3 tags representing the main clinical topics (e.g. 'Cardiology', 'Medication Safety', 'Diagnostics').\n"
            "4. A float quality score (0.0 to 1.0) representing the clarity and completeness of the response.\n\n"
            "Respond ONLY with a JSON object containing keys: 'suggested_questions', 'title', 'tags', 'quality_score'."
        )

        try:
            # We enforce json format using generate_json
            result = await self.groq_service.generate_json(
                prompt=prompt,
                system_prompt="You are a clinical intelligence agent. You must output a JSON object containing the keys: 'suggested_questions' (list of strings), 'title' (string), 'tags' (list of strings), and 'quality_score' (float)."
            )
            raw_content = result.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            
            # Sanitize outputs with defaults if needed
            return {
                "suggested_questions": parsed.get("suggested_questions", [
                    "Can you tell me more about my diagnostics?",
                    "Are there any drug safety concerns?",
                    "When is my next clinical appointment?"
                ])[:5],
                "title": parsed.get("title", "Clinical Consultation").strip(),
                "tags": parsed.get("tags", ["General Health"]),
                "quality_score": float(parsed.get("quality_score", 0.95))
            }
        except Exception as e:
            logger.exception(f"Failed to generate conversation intelligence details: {e}")
            # Fallback values
            return {
                "suggested_questions": [
                    "Can you tell me more about my diagnostics?",
                    "Are there any drug safety concerns?",
                    "When is my next clinical appointment?"
                ],
                "title": "Clinical Consultation",
                "tags": ["General Health"],
                "quality_score": 0.9
            }

    async def update_session_title_if_untitled(
        self,
        session_id: str,
        generated_title: str
    ) -> None:
        """Updates the chat title in MongoDB if it is currently a generic placeholder"""
        try:
            session = await self.chat_session_repository.get(session_id)
            if session and session.title in ("New Chat", "Untitled Chat", "Untitled Session", "New Conversation"):
                update_schema = ChatSessionUpdate(title=generated_title)
                await self.chat_session_repository.update(session_id, update_schema)
                logger.info(f"Updated session title to '{generated_title}' for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to update session title automatically: {e}")
