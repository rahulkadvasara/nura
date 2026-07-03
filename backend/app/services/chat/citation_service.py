"""
Nura - Chat Citation Service
Extracts and formats RAG retrieval references for UI display
"""

import logging
from typing import List, Dict, Any

from app.schemas.chat import CitationResponse
from app.repositories.chat_message_repository import ChatMessageRepository

logger = logging.getLogger(__name__)


class CitationService:
    """Formats raw database citation structures into standard schema schemas"""

    def __init__(self, chat_message_repository: ChatMessageRepository):
        self.chat_message_repository = chat_message_repository

    async def get_message_citations(
        self,
        message_id: str,
        patient_id: str
    ) -> List[CitationResponse]:
        """
        Retrieves the citations list for a specific message, mapping fields to
        the structured CitationResponse format.
        """
        msg = await self.chat_message_repository.get(message_id)
        if not msg:
            raise ValueError("Message not found")
        if msg.patient_id != patient_id:
            raise PermissionError("Access forbidden to this message")

        raw_citations = msg.citations or []
        formatted_citations: List[CitationResponse] = []

        for cit in raw_citations:
            # Map database keys to schema names
            document_id = cit.get("document_id") or cit.get("collection") or "Record"
            source_name = cit.get("source") or cit.get("collection") or "Medical Data"
            page_val = cit.get("page_number")
            section_val = cit.get("section")
            score_val = cit.get("score")
            report_title_val = cit.get("report_title") or cit.get("title") or "Clinical Document"
            clickable_metadata_val = cit.get("metadata") or cit.get("source_metadata") or {}

            formatted_citations.append(
                CitationResponse(
                    document=str(document_id),
                    source=str(source_name),
                    page=page_val,
                    section=section_val,
                    confidence=score_val,
                    report_title=str(report_title_val),
                    clickable_metadata=clickable_metadata_val
                )
            )

        return formatted_citations
