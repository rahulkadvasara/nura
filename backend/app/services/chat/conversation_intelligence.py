"""
Nura - Conversation Intelligence Service
Uses AI to compile suggested follow-up questions, summaries, titles, and tags
"""

import json
import logging
from typing import Dict, Any, List, Optional
from app.services.groq_service import GroqService
from app.repositories.chat_session_repository import ChatSessionRepository
from app.models.chat import ChatSessionUpdate, MessageRole

logger = logging.getLogger(__name__)


class ConversationIntelligenceService:
    """Computes suggested follow-ups, auto-generates chat titles, and scores quality"""

    def __init__(self, groq_service: GroqService, chat_session_repository: ChatSessionRepository, chat_message_repository: Any = None):
        self.groq_service = groq_service
        self.chat_session_repository = chat_session_repository
        # Optional chat_message_repository injection for history retrieval
        self.chat_message_repository = chat_message_repository

    async def generate_intelligence(
        self,
        user_message: str,
        assistant_response: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uses Groq LLM to generate suggested follow-ups, conversation title, quality score, and tags
        in a single lightweight JSON response.
        """
        conversation_str = ""
        if session_id and self.chat_message_repository:
            try:
                messages = await self.chat_message_repository.get_by_session_id(session_id, limit=20, include_deleted=False)
                if messages:
                    conversation_str = "\n".join([
                        f"{(m.role.value if hasattr(m.role, 'value') else str(m.role)).upper()}: {m.content}"
                        for m in messages
                    ])
            except Exception as e:
                logger.warning(f"Could not retrieve session messages for context: {e}")

        if not conversation_str:
            conversation_str = f"USER: {user_message}\nASSISTANT: {assistant_response}"

        prompt = (
            f"Analyze the following clinical conversation history:\n\n"
            f"{conversation_str}\n\n"
            "Based on the dialogue history, please generate:\n"
            "1. An improved, descriptive title (3-5 words) summarizing the session topic.\n"
            "2. A 1-2 sentence summary of the main concerns/advice discussed.\n"
            "3. 2-3 tags representing the main medical/operational specialties involved (e.g. Cardiology, Medication Safety, General).\n"
            "4. A 2-3 word description of the last topic discussed.\n"
            "5. A single-word category from: ['Prescription', 'Symptoms', 'Appointment', 'Safety', 'General'].\n"
            "6. 3 suggested follow-up questions for the patient.\n"
            "7. A float quality score (0.0 to 1.0) representing the clarity and completeness of the response.\n\n"
            "Respond ONLY with a JSON object containing keys: 'title', 'summary', 'tags', 'last_topic', 'category', 'suggested_questions', 'quality_score'."
        )

        try:
            result = await self.groq_service.generate_json(
                prompt=prompt,
                system_prompt="You are a clinical intelligence agent. You must output a JSON object containing the keys: 'title' (string), 'summary' (string), 'tags' (list of strings), 'last_topic' (string), 'category' (string), 'suggested_questions' (list of strings), and 'quality_score' (float)."
            )
            raw_content = result.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            
            return {
                "suggested_questions": parsed.get("suggested_questions", [
                    "Can you tell me more about my diagnostics?",
                    "Are there any drug safety concerns?",
                    "When is my next clinical appointment?"
                ])[:5],
                "title": parsed.get("title", "Clinical Consultation").strip(),
                "summary": parsed.get("summary", "Clinical discussion").strip(),
                "tags": parsed.get("tags", ["General Health"]),
                "last_topic": parsed.get("last_topic", "General Consultation").strip(),
                "category": parsed.get("category", "General").strip(),
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
                "summary": "Clinical discussion",
                "tags": ["General Health"],
                "last_topic": "General Consultation",
                "category": "General",
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

    async def auto_update_session_metadata(self, session_id: str) -> Dict[str, Any]:
        """
        Runs intelligence updates, retrieves clinical categories/summaries from Groq,
        and saves these details inside the MongoDB session document.
        """
        try:
            session = await self.chat_session_repository.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found for metadata updates")
                return {}

            if not self.chat_message_repository:
                return {}

            messages = await self.chat_message_repository.get_by_session_id(session_id, limit=20, include_deleted=False)
            if not messages:
                return {}

            user_message = ""
            assistant_response = ""
            for m in reversed(messages):
                if m.role == MessageRole.USER and not user_message:
                    user_message = m.content
                elif m.role == MessageRole.ASSISTANT and not assistant_response:
                    assistant_response = m.content
                if user_message and assistant_response:
                    break

            intel = await self.generate_intelligence(user_message, assistant_response, session_id)
            
            metadata = dict(session.metadata or {})
            metadata["summary"] = intel.get("summary", "")
            metadata["tags"] = intel.get("tags", [])
            metadata["last_topic"] = intel.get("last_topic", "")
            metadata["category"] = intel.get("category", "General")
            metadata["suggested_questions"] = intel.get("suggested_questions", [])

            update_payload = ChatSessionUpdate(
                title=intel.get("title", session.title),
                metadata=metadata
            )
            await self.chat_session_repository.update(session_id, update_payload)
            logger.info(f"Session {session_id} metadata and title dynamically updated in background.")
            return intel
        except Exception as e:
            logger.error(f"Failed to run auto-update session metadata: {e}")
            return {}
