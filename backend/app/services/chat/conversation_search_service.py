"""
Nura - Conversation Search Service
Provides regex full-text search across session metadata and message logs
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId

from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository
from app.schemas.chat import SearchHit, ConversationSearchResponse

logger = logging.getLogger(__name__)


def highlight_text(text: str, query: str) -> str:
    """Extract a matching snippet and enclose the matched query in HTML <mark> tags"""
    if not query:
        return text[:100]
    
    # Escape query for safe regex compile
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return text[:100]
        
    start = max(0, match.start() - 50)
    end = min(len(text), match.end() + 50)
    snippet = text[start:end]
    
    # Search again inside the snippet to apply highlight
    sub_match = pattern.search(snippet)
    if sub_match:
        matched_str = sub_match.group(0)
        snippet = snippet[:sub_match.start()] + f"<mark>{matched_str}</mark>" + snippet[sub_match.end():]
        
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet


class ConversationSearchService:
    """Full-text search provider for chat history"""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository
    ):
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository

    async def search_conversations(
        self,
        patient_id: str,
        query: str,
        session_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        favorites: Optional[bool] = None,
        archived: Optional[bool] = None,
        agent: Optional[str] = None
    ) -> ConversationSearchResponse:
        """
        Executes query matching across session titles, summaries, and message content
        applying date, favorite state, and agent filter constraints.
        """
        # 1. Fetch matching sessions based on constraints
        session_filter: Dict[str, Any] = {
            "patient_id": patient_id,
            "status": {"$ne": "DELETED"}
        }

        if session_id:
            session_filter["_id"] = ObjectId(session_id) if ObjectId.is_valid(session_id) else session_id
        if favorites is not None:
            session_filter["pinned"] = favorites
        if archived is not None:
            session_filter["archived"] = archived
        if date_from:
            session_filter["created_at"] = {"$gte": date_from}
        if date_to:
            session_filter.setdefault("created_at", {})["$lte"] = date_to
        if agent:
            session_filter["last_agent_used"] = agent

        # Fetch all matching sessions from DB
        sessions = []
        cursor = self.chat_session_repository.collection.find(session_filter)
        docs = await cursor.to_list(length=1000)
        for doc in docs:
            sessions.append(self.chat_session_repository.model_class.from_mongo(doc))

        if not sessions:
            return ConversationSearchResponse(results=[])

        session_ids = [s.id for s in sessions]
        session_map = {s.id: s for s in sessions}

        hits: List[SearchHit] = []
        query_esc = re.escape(query)

        # 2. Check session title/summary matching
        for sess in sessions:
            summary = sess.metadata.get("summary", "")
            tags = sess.metadata.get("tags", [])
            
            match_title = re.search(query_esc, sess.title, re.IGNORECASE)
            match_summary = re.search(query_esc, summary, re.IGNORECASE)
            match_tags = any(re.search(query_esc, t, re.IGNORECASE) for t in tags)

            if match_title or match_summary or match_tags:
                snippet_text = summary if match_summary else (f"Tags: {', '.join(tags)}" if match_tags else sess.title)
                hits.append(
                    SearchHit(
                        session_id=sess.id,
                        session_title=sess.title,
                        message_id=None,
                        role=None,
                        content=snippet_text,
                        highlighted_snippet=highlight_text(snippet_text, query),
                        timestamp=sess.last_message_at
                    )
                )

        # 3. Query all active (non-deleted) messages in these session IDs matching the query content
        message_filter = {
            "session_id": {"$in": session_ids},
            "deleted": {"$ne": True},
            "content": {"$regex": query_esc, "$options": "i"}
        }

        msg_cursor = self.chat_message_repository.collection.find(message_filter)
        m_docs = await msg_cursor.to_list(length=1000)
        for m_doc in m_docs:
            msg = self.chat_message_repository.model_class.from_mongo(m_doc)
            sess = session_map.get(msg.session_id)
            if sess:
                hits.append(
                    SearchHit(
                        session_id=msg.session_id,
                        session_title=sess.title,
                        message_id=msg.id,
                        role=msg.role.value if hasattr(msg.role, "value") else str(msg.role),
                        content=msg.content,
                        highlighted_snippet=highlight_text(msg.content, query),
                        timestamp=msg.created_at
                    )
                )

        # Sort hits chronologically descending (most recent first)
        hits.sort(key=lambda h: h.timestamp, reverse=True)
        return ConversationSearchResponse(results=hits)
