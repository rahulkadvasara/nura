"""
Nura - Conversation Export Service
Provides Markdown, JSON, and PDF document exports for chat session logs
"""

import io
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models.chat import ChatSessionInDB, ChatMessageInDB
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.chat_message_repository import ChatMessageRepository


class ExportService:
    """Orchestrates document exports for patient chat transcripts"""

    def __init__(
        self,
        chat_session_repository: ChatSessionRepository,
        chat_message_repository: ChatMessageRepository
    ):
        self.chat_session_repository = chat_session_repository
        self.chat_message_repository = chat_message_repository

    async def get_export_data(self, session_id: str, patient_id: str) -> Dict[str, Any]:
        """Fetches and verifies session and active messages for export"""
        session = await self.chat_session_repository.get(session_id)
        if not session or session.patient_id != patient_id:
            raise PermissionError("Access forbidden or session not found")
            
        messages = await self.chat_message_repository.get_by_session_id(
            session_id,
            limit=200,
            include_deleted=False
        )
        return {
            "session": session,
            "messages": messages
        }

    def export_as_markdown(self, session: ChatSessionInDB, messages: List[ChatMessageInDB]) -> str:
        """Formats the session transcript as Markdown"""
        summary = session.metadata.get("summary", "No summary compiled.")
        lines = [
            f"# Conversation Export: {session.title}",
            f"**Date:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            f"**Topic Summary:** {summary}",
            f"**Specialty Category:** {session.metadata.get('category', 'General')}",
            f"**Tags:** {', '.join(session.metadata.get('tags', []))}",
            "\n---\n"
        ]

        for m in messages:
            role_name = "Patient" if m.role == "USER" else f"AI Agent ({m.metadata.get('agent', 'Nura')})"
            time_str = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"### {role_name} - *{time_str}*")
            lines.append(m.content)
            
            if m.citations:
                lines.append("\n**Citations & Sources:**")
                for cit in m.citations:
                    doc = cit.get("document_id") or cit.get("collection") or "Record"
                    src = cit.get("source") or "Medical Data"
                    p = f" (Page {cit.get('page_number')})" if cit.get("page_number") else ""
                    sec = f", Section: {cit.get('section')}" if cit.get("section") else ""
                    lines.append(f"- {src}: {doc}{p}{sec}")
            lines.append("")

        return "\n".join(lines)

    def export_as_json(self, session: ChatSessionInDB, messages: List[ChatMessageInDB]) -> str:
        """Formats the session transcript as JSON"""
        data = {
            "session_id": session.id,
            "title": session.title,
            "patient_id": session.patient_id,
            "summary": session.metadata.get("summary", ""),
            "tags": session.metadata.get("tags", []),
            "category": session.metadata.get("category", "General"),
            "last_topic": session.metadata.get("last_topic", ""),
            "created_at": session.created_at.isoformat(),
            "messages": [
                {
                    "id": m.id,
                    "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                    "content": m.content,
                    "citations": m.citations,
                    "agent": m.metadata.get("agent"),
                    "intent": m.metadata.get("intent"),
                    "timestamp": m.created_at.isoformat()
                }
                for m in messages
            ]
        }
        return json.dumps(data, indent=2)

    def export_as_pdf(self, session: ChatSessionInDB, messages: List[ChatMessageInDB]) -> bytes:
        """Formats the session transcript as PDF bytes using ReportLab"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
        except ImportError:
            # Fallback text representation if reportlab is missing
            fallback_text = self.export_as_markdown(session, messages)
            return fallback_text.encode("utf-8")

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        story = []

        # Custom paragraph styles
        title_style = ParagraphStyle(
            'PDFTitle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0F766E'),
            spaceAfter=12
        )
        meta_style = ParagraphStyle(
            'PDFMeta',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=15
        )
        body_style = ParagraphStyle(
            'PDFBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#1E293B'),
        )
        citation_style = ParagraphStyle(
            'PDFCitation',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#475569'),
        )

        story.append(Paragraph(f"Nura Transcript: {session.title}", title_style))
        
        summary_text = session.metadata.get("summary", "No summary compiled.")
        meta_html = (
            f"<b>Date:</b> {session.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC<br/>"
            f"<b>Category:</b> {session.metadata.get('category', 'General')}<br/>"
            f"<b>Tags:</b> {', '.join(session.metadata.get('tags', []))}<br/>"
            f"<b>Summary:</b> {summary_text}"
        )
        story.append(Paragraph(meta_html, meta_style))
        story.append(Spacer(1, 10))

        for m in messages:
            role_label = "Patient" if m.role == "USER" else f"AI Agent ({m.metadata.get('agent', 'Nura')})"
            role_color = '#0F766E' if m.role == "USER" else '#6D28D9'
            
            header_html = f"<b><font color='{role_color}'>{role_label}</font></b> &nbsp;&nbsp;<font color='#94A3B8'>{m.created_at.strftime('%Y-%m-%d %H:%M:%S')}</font>"
            story.append(Paragraph(header_html, body_style))
            story.append(Spacer(1, 4))
            
            content_cleaned = m.content.replace("\n", "<br/>")
            story.append(Paragraph(content_cleaned, body_style))
            
            if m.citations:
                story.append(Spacer(1, 6))
                cit_lines = ["<b>Citations:</b>"]
                for cit in m.citations:
                    doc = cit.get("document_id") or cit.get("collection") or "Record"
                    src = cit.get("source") or "Medical Data"
                    p = f" (Page {cit.get('page_number')})" if cit.get("page_number") else ""
                    sec = f", Section: {cit.get('section')}" if cit.get("section") else ""
                    cit_lines.append(f"- {src}: {doc}{p}{sec}")
                story.append(Paragraph("<br/>".join(cit_lines), citation_style))
                
            story.append(Spacer(1, 15))

        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_bytes
