"""
Nura - Retrieval Evaluation Service
Computes precision, recall, duplicate rate, citation quality, and context utilization.
Stores evaluation history in MongoDB.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.db.mongodb import get_database
from app.services.retrieval_service import RetrievalService
from app.services.context_assembly_service import ContextAssemblyService

class RetrievalEvaluationService:
    """Service to evaluate RAG quality metrics for query execution runs"""

    def __init__(
        self,
        retrieval_service: RetrievalService,
        context_assembly_service: ContextAssemblyService
    ):
        self.retrieval_service = retrieval_service
        self.context_assembly_service = context_assembly_service

    async def evaluate_query(
        self,
        query: str,
        patient_id: Optional[str] = None,
        collections: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        ground_truth_doc_ids: Optional[List[str]] = None,
        top_k: int = 5,
        score_threshold: float = 0.3,
        token_budget: int = 4000
    ) -> Dict[str, Any]:
        """
        Evaluate retrieval metrics for a specific search query.
        Calculates Precision, Recall, Citation Quality, Duplicate Rate, and Context Utilization.
        """
        start_time = time.perf_counter()
        target_cols = collections or ["patient_reports", "medical_knowledge", "drug_knowledge"]

        # 1. Run Retrieval
        ret_filters = dict(filters or {})
        if patient_id:
            ret_filters["patient_id"] = patient_id

        retrieval_res = await self.retrieval_service.retrieve_multiple(
            query=query,
            collections=target_cols,
            filters=ret_filters,
            top_k=top_k,
            score_threshold=score_threshold
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        hits = retrieval_res.get("results", [])
        chunks_found = retrieval_res.get("chunks_found", 0)
        duplicates_removed = retrieval_res.get("duplicates_removed", 0)

        # 2. Precision: portions of hits with normalized score >= 0.70
        relevant_hits = [h for h in hits if h.get("score", 0.0) >= 0.70]
        precision = len(relevant_hits) / len(hits) if hits else 0.0

        # 3. Recall
        retrieved_doc_ids = {h["metadata"].get("document_id") for h in hits if h.get("metadata")}
        retrieved_doc_ids.discard(None)
        if ground_truth_doc_ids:
            gt_set = set(ground_truth_doc_ids)
            recall = len(retrieved_doc_ids.intersection(gt_set)) / len(gt_set) if gt_set else 1.0
        else:
            # Heuristic recall: portion of relevant hits in the retrieved set
            recall = len(relevant_hits) / top_k if top_k > 0 else 0.0

        # 4. Citation Quality: proportion of hits with valid document_id and chunk metadata
        valid_citations = 0
        for h in hits:
            meta = h.get("metadata") or {}
            citations = h.get("citations") or {}
            if (meta.get("document_id") or citations.get("document_id")) and (meta.get("chunk_index") is not None or citations.get("chunk_index") is not None):
                valid_citations += 1
        citation_quality = valid_citations / len(hits) if hits else 1.0

        # 5. Duplicate Rate
        total_found = len(hits) + duplicates_removed
        duplicate_rate = duplicates_removed / total_found if total_found > 0 else 0.0

        # 6. Context Utilization: Assemble context and measure token space used
        assembly_res = await self.context_assembly_service.assemble(
            query=query,
            patient_id=patient_id,
            token_budget=token_budget,
            collections=target_cols,
            filters=filters
        )
        assembled_tokens = assembly_res.get("estimated_tokens", 0)
        context_utilization = min(1.0, assembled_tokens / token_budget) if token_budget > 0 else 0.0

        # 7. Chunk Relevance: Average similarity score
        avg_relevance = sum(h.get("score", 0.0) for h in hits) / len(hits) if hits else 0.0

        eval_report = {
            "query": query,
            "patient_id": patient_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "precision": precision,
                "recall": recall,
                "latency_ms": latency_ms,
                "citation_quality": citation_quality,
                "chunk_relevance": avg_relevance,
                "duplicate_rate": duplicate_rate,
                "context_utilization": context_utilization
            },
            "parameters": {
                "collections": target_cols,
                "top_k": top_k,
                "score_threshold": score_threshold,
                "token_budget": token_budget
            },
            "retrieval_summary": {
                "hits_count": len(hits),
                "chunks_found": chunks_found,
                "duplicates_removed": duplicates_removed,
                "assembled_sections": list(assembly_res.get("sections", {}).keys())
            }
        }

        # Save to MongoDB
        try:
            db = get_database()
            await db.rag_evaluations.insert_one(eval_report.copy())
        except Exception as e:
            # Gracefully handle if DB is unavailable/not connected
            pass

        # Remove MongoDB Object ID if populated in copy
        eval_report.pop("_id", None)
        return eval_report

    async def get_evaluation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent evaluation records from MongoDB"""
        try:
            db = get_database()
            cursor = db.rag_evaluations.find().sort("timestamp", -1).limit(limit)
            history = []
            async for doc in cursor:
                doc.pop("_id", None)
                history.append(doc)
            return history
        except Exception:
            return []


# Singleton dependency helper
_eval_service_instance: Optional[RetrievalEvaluationService] = None


def get_retrieval_evaluation_service() -> RetrievalEvaluationService:
    """Retrieve singleton instance of RetrievalEvaluationService"""
    global _eval_service_instance
    if _eval_service_instance is None:
        from app.core.dependencies import get_retrieval_service, get_context_assembly_service
        ret_svc = get_retrieval_service()
        ctx_svc = get_context_assembly_service()
        _eval_service_instance = RetrievalEvaluationService(
            retrieval_service=ret_svc,
            context_assembly_service=ctx_svc
        )
    return _eval_service_instance
