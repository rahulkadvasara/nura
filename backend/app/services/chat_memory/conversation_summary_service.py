"""
Nura - Conversation Summarization Service
Uses AI to compile RAG-optimized clinical summaries, medical entities, and keywords
"""

import json
import logging
import time
from typing import Dict, Any, List

from app.services.groq_service import GroqService
from app.services.chat_memory.telemetry import memory_telemetry

logger = logging.getLogger(__name__)


class ConversationSummaryService:
    """Invokes Groq service to compute dense vector search summaries and extract structured health parameters"""

    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    async def generate_summary(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Calls Groq to generate a dense semantic summary, clinical keywords, and medical entities
        from a list of chat messages. Logs latency metrics to the telemetry singleton.
        """
        conversation_text = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages])
        
        prompt = (
            f"Review this conversation between a clinical assistant and a patient:\n\n"
            f"{conversation_text}\n\n"
            "Analyze and summarize the discussion for clinical retention. You must respond with a JSON object containing precisely these keys:\n"
            "- 'summary': A dense, detailed paragraph optimized for vector search. Focus on symptoms, medications, diagnoses, advice given, and follow-up plans. Avoid conversational filler.\n"
            "- 'keywords': A list of 5-8 relevant search terms (symptoms, drugs, topics).\n"
            "- 'entities': A list of clinical terms (e.g., diagnoses, medications, lab tests, active symptoms).\n"
            "- 'medications': A list of medications mentioned.\n"
            "- 'symptoms': A list of active symptoms discussed.\n"
            "- 'diagnoses': A list of diagnostic terms discussed.\n"
            "- 'recommendations': A list of advice or warnings given by the assistant.\n"
            "- 'followups': A list of scheduled actions, appointments, or recheck plans."
        )

        start_time = time.perf_counter()
        try:
            result = await self.groq_service.generate_json(
                prompt=prompt,
                system_prompt="You are a senior medical records AI. You summarize conversation transcripts into dense RAG documents and extract structured clinical fields as requested. You must output valid JSON."
            )
            raw_content = result.choices[0].message.content or "{}"
            parsed = json.loads(raw_content)
            
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            memory_telemetry.record_latencies(sum_lat=latency_ms)

            return {
                "summary": parsed.get("summary", "Conversation summary unavailable."),
                "keywords": parsed.get("keywords", []),
                "entities": parsed.get("entities", []),
                "medications": parsed.get("medications", []),
                "symptoms": parsed.get("symptoms", []),
                "diagnoses": parsed.get("diagnoses", []),
                "recommendations": parsed.get("recommendations", []),
                "followups": parsed.get("followups", []),
            }

        except Exception as e:
            logger.exception(f"Failed to generate conversation summary: {e}")
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            memory_telemetry.record_latencies(sum_lat=latency_ms)
            
            # Safe fallback structure
            return {
                "summary": "Clinical conversation regarding health questions.",
                "keywords": ["consultation"],
                "entities": [],
                "medications": [],
                "symptoms": [],
                "diagnoses": [],
                "recommendations": [],
                "followups": [],
            }
