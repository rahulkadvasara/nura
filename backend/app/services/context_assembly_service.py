"""
Nura - Context Assembly Service
Business logic for compiling, ranking, compressing, and budgeting patient context
and semantic vector retrieval chunks for LLM consumption.
"""

import time
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

from app.core.ai_config import AISettings, ai_settings
from app.services.patient_context_service import PatientContextService
from app.services.retrieval_service import RetrievalService
from app.schemas.context_assembly import ContextAssemblyRequest, ContextAssemblyResponse
from app.utils.ai import context_assembly_metrics

logger = logging.getLogger("nura.ai.context_assembly")


class AssembledChunk:
    """Internal model for grouping and ranking context content items"""
    def __init__(
        self,
        content: str,
        score: Optional[float] = None,
        date: Optional[datetime] = None,
        citation_id: Optional[str] = None,
        is_mongodb: bool = False
    ):
        self.content = content
        self.score = score
        self.date = date
        self.citation_id = citation_id
        self.is_mongodb = is_mongodb


class ContextAssemblyService:
    """Context Assembly Engine responsible for constructing the best possible prompt context"""

    def __init__(
        self,
        patient_context_service: PatientContextService,
        retrieval_service: RetrievalService,
        settings: AISettings = ai_settings
    ):
        self.patient_context_service = patient_context_service
        self.retrieval_service = retrieval_service
        self.settings = settings

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens using the standard len(text) // 4 character-to-token heuristic"""
        if not text:
            return 0
        return len(text) // 4

    def compress(self, text: str) -> str:
        """
        Compresses text deterministically:
        - Removes duplicate sentences case-insensitively
        - Cleans consecutive whitespace and merges paragraphs
        - Preserves citation index tags
        """
        if not text:
            return ""

        # Whitespace cleanup: replace tabs and consecutive spaces, clean newlines
        lines = [line.strip() for line in text.splitlines()]
        lines = [l for l in lines if l]
        cleaned_text = " ".join(lines)

        # Sentence split (delimiters: . ? ! followed by space or end of string)
        sentence_ends = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_ends.split(cleaned_text)

        seen_sentences = set()
        unique_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            
            # Normalize sentence for deduplication (strip citation tags [Ref X] and compare alphanumeric lowercase)
            s_norm = re.sub(r'\[Ref\s+\d+\]', '', s_clean)
            s_norm = re.sub(r'\[Citation\s+\d+\]', '', s_norm)
            norm_key = "".join(c.lower() for c in s_norm if c.isalnum())

            if norm_key not in seen_sentences:
                seen_sentences.add(norm_key)
                unique_sentences.append(s_clean)

        compressed = " ".join(unique_sentences)
        compressed = re.sub(r'\s+', ' ', compressed).strip()
        return compressed

    def rank(
        self,
        chunks: List[Dict[str, Any]],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, List[AssembledChunk]], Dict[str, Any]]:
        """
        Groups and ranks context sections from MongoDB context and retrieval chunks.
        Maintains citation mapping for vector search chunks.
        """
        sections: Dict[str, List[AssembledChunk]] = {
            "PATIENT SUMMARY": [],
            "CURRENT CONDITION": [],
            "REPORT FINDINGS": [],
            "CONSULTATION HISTORY": [],
            "PRESCRIPTIONS": [],
            "MEDICAL KNOWLEDGE": [],
            "DRUG KNOWLEDGE": [],
            "DOCTOR INFORMATION": [],
            "CHAT MEMORY": []
        }

        citation_map = {}
        citation_counter = 1

        # 1. Map Qdrant semantic search chunks
        for chunk in chunks:
            content = chunk.get("content", "").strip()
            if not content:
                continue

            score = chunk.get("score", 0.0)
            col_name = chunk.get("collection", "")
            doc_type = chunk.get("document_type", "").upper()
            metadata = chunk.get("metadata", {})

            # Extract date if available for recency sorting
            created_at_str = metadata.get("created_at") or metadata.get("indexed_at")
            date_val = None
            if created_at_str:
                try:
                    # Strip Z if needed, parse ISO timestamp
                    if created_at_str.endswith("Z"):
                        created_at_str = created_at_str[:-1] + "+00:00"
                    date_val = datetime.fromisoformat(created_at_str)
                except Exception:
                    pass

            # Create citation
            citation_id = f"Ref {citation_counter}"
            citation_counter += 1
            citation_map[citation_id] = {
                "source": metadata.get("source", "qdrant"),
                "collection": col_name,
                "document_id": metadata.get("document_id"),
                "chunk_id": metadata.get("chunk_id") or chunk.get("id"),
                "page_number": metadata.get("page_number", 1),
                "score": score
            }

            # Map to section based on collection name / document type
            target_section = "MEDICAL KNOWLEDGE"
            if col_name == "patient_reports" or doc_type == "REPORT":
                target_section = "REPORT FINDINGS"
            elif col_name == "chat_memory" or doc_type == "CHAT_MEMORY":
                target_section = "CHAT MEMORY"
            elif col_name == "medical_knowledge" or doc_type == "MEDICAL_ARTICLE":
                target_section = "MEDICAL KNOWLEDGE"
            elif col_name == "drug_knowledge" or doc_type == "DRUG_DATASET":
                target_section = "DRUG KNOWLEDGE"
            elif col_name == "doctor_knowledge" or doc_type == "DOCTOR_PROFILE":
                target_section = "DOCTOR INFORMATION"

            sections[target_section].append(
                AssembledChunk(
                    content=content,
                    score=score,
                    date=date_val,
                    citation_id=citation_id,
                    is_mongodb=False
                )
            )

        # 2. Map MongoDB patient context summaries
        if patient_context:
            # Basic Profile -> PATIENT SUMMARY
            profile = patient_context.get("patient_profile")
            if profile:
                profile_desc = f"Patient Profile: Name: {profile.get('full_name')}, Email: {profile.get('email')}, Phone: {profile.get('phone')}."
                sections["PATIENT SUMMARY"].append(
                    AssembledChunk(content=profile_desc, is_mongodb=True)
                )

            # Longitudinal summary -> PATIENT SUMMARY
            med_summary = patient_context.get("medical_summary")
            if med_summary:
                sections["PATIENT SUMMARY"].append(
                    AssembledChunk(content=f"Medical Summary: {med_summary}", is_mongodb=True)
                )

            # Lifestyle notes -> PATIENT SUMMARY
            lifestyle = patient_context.get("lifestyle_notes")
            if lifestyle:
                sections["PATIENT SUMMARY"].append(
                    AssembledChunk(content=f"Lifestyle Notes: {lifestyle}", is_mongodb=True)
                )

            # Risk factors -> PATIENT SUMMARY
            risks = patient_context.get("risk_factors")
            if risks:
                sections["PATIENT SUMMARY"].append(
                    AssembledChunk(content=f"Health Risk Factors: {', '.join(risks)}", is_mongodb=True)
                )

            # Emergency info -> PATIENT SUMMARY
            emerg = patient_context.get("emergency_information")
            if emerg:
                sections["PATIENT SUMMARY"].append(
                    AssembledChunk(content=f"EMERGENCY INFORMATION: {emerg}", is_mongodb=True)
                )

            # Diagnoses & Conditions -> CURRENT CONDITION
            conditions = patient_context.get("current_conditions")
            if conditions:
                sections["CURRENT CONDITION"].append(
                    AssembledChunk(content=f"Active Diagnoses: {', '.join(conditions)}", is_mongodb=True)
                )

            # Allergies -> CURRENT CONDITION
            allergies = patient_context.get("medication_allergies") or patient_context.get("drug_allergies")
            if allergies:
                sections["CURRENT CONDITION"].append(
                    AssembledChunk(content=f"Allergies: {', '.join(allergies)}", is_mongodb=True)
                )

            # History -> CURRENT CONDITION
            history = patient_context.get("past_medical_history")
            if history:
                sections["CURRENT CONDITION"].append(
                    AssembledChunk(content=f"Past Medical History: {', '.join(history)}", is_mongodb=True)
                )

            # Reminders -> CURRENT CONDITION
            reminders = patient_context.get("reminder_summary")
            if reminders:
                reminder_lines = []
                for r in reminders:
                    reminder_lines.append(f"Reminder: {r.get('title')} ({r.get('description') or ''}) Scheduled: {r.get('scheduled_time')}")
                sections["CURRENT CONDITION"].append(
                    AssembledChunk(content="Active Reminders: " + "; ".join(reminder_lines), is_mongodb=True)
                )

            # Health Insights -> CURRENT CONDITION
            insights = patient_context.get("recent_health_insights")
            if insights:
                insight_lines = []
                for i in insights:
                    insight_lines.append(f"{i.get('title')} - {i.get('description')} (Severity: {i.get('severity')})")
                sections["CURRENT CONDITION"].append(
                    AssembledChunk(content="AI Health Insights: " + "; ".join(insight_lines), is_mongodb=True)
                )

            # Reports Summaries -> REPORT FINDINGS
            reports = patient_context.get("lab_reports_summary")
            if reports:
                for r in reports:
                    dt = None
                    try:
                        dt = datetime.fromisoformat(r.get("created_at"))
                    except Exception:
                        pass
                    sections["REPORT FINDINGS"].append(
                        AssembledChunk(
                            content=f"Lab/Imaging Report Summary: {r.get('report_type')} (Risk: {r.get('risk_level')}, Date: {r.get('created_at')}): {r.get('ai_summary')}",
                            date=dt,
                            is_mongodb=True
                        )
                    )

            # Consultations -> CONSULTATION HISTORY
            consultations = patient_context.get("consultations_summary")
            if consultations:
                for c in consultations:
                    dt = None
                    try:
                        dt = datetime.fromisoformat(c.get("created_at"))
                    except Exception:
                        pass
                    sections["CONSULTATION HISTORY"].append(
                        AssembledChunk(
                            content=f"Doctor Consultation notes (Date: {c.get('created_at')}): Diagnosis: {c.get('diagnosis')}. Recommendations: {c.get('recommendations')}. Notes: {c.get('consultation_notes')}",
                            date=dt,
                            is_mongodb=True
                        )
                    )

            # Prescriptions -> PRESCRIPTIONS
            prescriptions = patient_context.get("prescriptions_summary")
            if prescriptions:
                for p in prescriptions:
                    dt = None
                    try:
                        dt = datetime.fromisoformat(p.get("created_at"))
                    except Exception:
                        pass
                    meds_list = []
                    for m in p.get("medications", []):
                        meds_list.append(f"{m.get('drug_name')} (Dosage: {m.get('dosage')}, Freq: {m.get('frequency')}, Dur: {m.get('duration')})")
                    sections["PRESCRIPTIONS"].append(
                        AssembledChunk(
                            content=f"Prescription (Date: {p.get('created_at')}): medications prescribed: {'; '.join(meds_list)}. Instruction/Notes: {p.get('notes')}",
                            date=dt,
                            is_mongodb=True
                        )
                    )

        # 3. Sort each section's contents by semantic score descending, then date descending
        for sec_name, chunk_list in sections.items():
            # Sorting key: MongoDB records first (or score=1.0), then score, then date, then content to ensure determinism
            def sort_val(c: AssembledChunk):
                score_sort = c.score if c.score is not None else 1.0
                date_sort = c.date.timestamp() if c.date else 0.0
                return (-score_sort, -date_sort, c.content)

            chunk_list.sort(key=sort_val)

        return sections, citation_map

    def build_sections(self, ranked_data: Dict[str, List[AssembledChunk]]) -> Dict[str, str]:
        """Formats and serializes the ranked data into formatted section strings"""
        section_texts = {}
        for sec_name, chunks in ranked_data.items():
            if not chunks:
                continue

            lines = []
            for chunk in chunks:
                if chunk.citation_id:
                    lines.append(f"[{chunk.citation_id}] {chunk.content}")
                else:
                    lines.append(chunk.content)

            raw_text = "\n".join(lines)
            # Apply deterministic compression
            compressed_text = self.compress(raw_text)
            if compressed_text:
                section_texts[sec_name] = compressed_text

        return section_texts

    def _estimate_total_tokens(self, sections: Dict[str, str]) -> int:
        """Helper to compute token usage across all currently active sections"""
        combined = []
        for header, text in sections.items():
            combined.append(f"=== {header} ===")
            combined.append(text)
        return self.estimate_tokens("\n".join(combined))

    async def assemble(
        self,
        query: str,
        patient_id: Optional[str] = None,
        token_budget: Optional[int] = 4000,
        collections: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinates full context assembly workflow: retrieves patient summaries
        and vector chunks, ranks, applies token budget limits, compresses,
        and constructs final prompt context with citations metadata.
        """
        start_time = time.perf_counter()
        budget = token_budget or 4000

        try:
            # 1. Fetch MongoDB patient context if patient_id is present
            patient_context_response = None
            patient_context_dict = None
            if patient_id:
                # Retrieve large context bounds so assembly service controls fine pruning
                patient_context_response = await self.patient_context_service.assemble_context(
                    patient_id=patient_id,
                    token_budget=budget * 2
                )
                patient_context_dict = patient_context_response.model_dump()

            # 2. Retrieve semantic chunks from Qdrant vector store
            # Enforce patient_id metadata filter to prevent data leak across patient files
            retrieval_filters = dict(filters or {})
            if patient_id:
                retrieval_filters["patient_id"] = patient_id

            target_cols = collections
            if not target_cols:
                # Default to all standard vector collections
                target_cols = ["patient_reports", "chat_memory", "medical_knowledge", "drug_knowledge", "doctor_knowledge"]

            # Query Qdrant
            retrieval_res = await self.retrieval_service.retrieve_multiple(
                query=query,
                collections=target_cols,
                filters=retrieval_filters,
                top_k=8,  # Retrieve slightly more than top_k to select/filter down
                score_threshold=0.3
            )
            retrieved_chunks = retrieval_res.get("results", [])
            original_chunks_count = len(retrieved_chunks)

            # 3. Group and rank context sections, preserving citations
            ranked_sections, citation_map = self.rank(
                chunks=retrieved_chunks,
                patient_context=patient_context_dict
            )

            # 4. Perform iterative token budget management and reduction
            # Start with fully populated sections
            sections = self.build_sections(ranked_sections)
            total_original_chars = sum(len(text) for text in sections.values())

            # Perform reduction loop if we exceed budget
            # Steps to reduce:
            # 1. Reduce/compress CHAT MEMORY
            # 2. Reduce DOCTOR INFORMATION, DRUG KNOWLEDGE, MEDICAL KNOWLEDGE
            # 3. Reduce PRESCRIPTIONS, CONSULTATION HISTORY, REPORT FINDINGS
            # Keep PATIENT SUMMARY and CURRENT CONDITION intact
            while self._estimate_total_tokens(sections) > budget:
                # Try popping from lowest priority collections first
                reduced_any = False

                # Level 1: CHAT MEMORY
                if ranked_sections.get("CHAT MEMORY"):
                    ranked_sections["CHAT MEMORY"].pop()  # Pop lowest score chunk
                    reduced_any = True
                
                # Level 2: Doctor information, Drug, Medical knowledge
                elif ranked_sections.get("DOCTOR INFORMATION"):
                    ranked_sections["DOCTOR INFORMATION"].pop()
                    reduced_any = True
                elif ranked_sections.get("DRUG KNOWLEDGE"):
                    ranked_sections["DRUG KNOWLEDGE"].pop()
                    reduced_any = True
                elif ranked_sections.get("MEDICAL KNOWLEDGE"):
                    ranked_sections["MEDICAL KNOWLEDGE"].pop()
                    reduced_any = True

                # Level 3: Prescriptions, Consultation, Reports findings
                elif ranked_sections.get("PRESCRIPTIONS"):
                    ranked_sections["PRESCRIPTIONS"].pop()
                    reduced_any = True
                elif ranked_sections.get("CONSULTATION HISTORY"):
                    ranked_sections["CONSULTATION HISTORY"].pop()
                    reduced_any = True
                elif ranked_sections.get("REPORT FINDINGS"):
                    # For report findings, check if there is more than 1 chunk/summary
                    if len(ranked_sections["REPORT FINDINGS"]) > 1:
                        ranked_sections["REPORT FINDINGS"].pop()
                        reduced_any = True

                # Rebuild sections and check if we successfully reduced size
                if reduced_any:
                    sections = self.build_sections(ranked_sections)
                else:
                    # Cannot reduce any further without deleting PATIENT SUMMARY
                    break

            # Calculate metrics
            assembly_time = (time.perf_counter() - start_time) * 1000.0
            estimated_tokens = self._estimate_total_tokens(sections)

            # Filter citations to include only those tags that are preserved in final sections text
            active_citation_ids = set()
            for text in sections.values():
                for ref in re.findall(r'\[Ref\s+(\d+)\]', text):
                    active_citation_ids.add(f"Ref {ref}")

            final_citations = {cit_id: metadata for cit_id, metadata in citation_map.items() if cit_id in active_citation_ids}
            removed_chunks_count = original_chunks_count - len([c for col in ranked_sections.values() for c in col if not c.is_mongodb])

            final_chars = sum(len(text) for text in sections.values())
            compression_ratio = (final_chars / total_original_chars) if total_original_chars > 0 else 1.0

            # Record telemetry metrics
            context_assembly_metrics.record_assembly(
                latency_ms=assembly_time,
                success=True,
                original_chunks=original_chunks_count,
                removed_chunks=removed_chunks_count,
                compression_ratio=compression_ratio,
                estimated_tokens=estimated_tokens,
                sections=list(sections.keys())
            )

            # Response structure
            return {
                "sections": sections,
                "citations": final_citations,
                "estimated_tokens": estimated_tokens,
                "compression_ratio": compression_ratio,
                "assembly_time": assembly_time,
                "metadata": {
                    "query": query,
                    "patient_id": patient_id,
                    "collections_queried": target_cols,
                    "original_chunks": original_chunks_count,
                    "removed_chunks": removed_chunks_count,
                    "total_original_chars": total_original_chars,
                    "total_final_chars": final_chars
                }
            }

        except Exception as e:
            assembly_time = (time.perf_counter() - start_time) * 1000.0
            context_assembly_metrics.record_assembly(
                latency_ms=assembly_time,
                success=False
            )
            logger.error(f"Context Assembly process failed: {str(e)}")
            raise e


# Singleton instance helper
_context_assembly_service_instance = None


def get_context_assembly_service() -> ContextAssemblyService:
    """Retrieve singleton instance of ContextAssemblyService"""
    global _context_assembly_service_instance
    if _context_assembly_service_instance is None:
        from app.core.dependencies import get_patient_context_service, get_retrieval_service
        pt_ctx_svc = get_patient_context_service()
        ret_svc = get_retrieval_service()
        _context_assembly_service_instance = ContextAssemblyService(
            patient_context_service=pt_ctx_svc,
            retrieval_service=ret_svc,
            settings=ai_settings
        )
    return _context_assembly_service_instance
