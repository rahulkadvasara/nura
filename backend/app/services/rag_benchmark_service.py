"""
Nura - RAG Benchmark Service
Automated benchmark suite for measuring latency, precision, and cache utilization across query categories.
Stores benchmark runs history in MongoDB.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.db.mongodb import get_database
from app.services.retrieval_evaluation_service import RetrievalEvaluationService

# 7 Standardized Benchmark Datasets
BENCHMARK_DATASET = [
    {
        "category": "Medical",
        "intent": "medical_question",
        "queries": [
            "What are the chronic complications of hypertension?",
            "What are the common symptoms of Type 2 Diabetes?",
            "How does chronic kidney disease progress over time?",
            "What is the treatment protocol for acute bronchitis?"
        ]
    },
    {
        "category": "Reports",
        "intent": "report_analysis",
        "queries": [
            "Explain high liver enzymes in my diagnostic report",
            "What do my lipid panel cholesterol numbers mean?",
            "Analyze my CBC test results for anemia indicators",
            "Explain the findings of my chest X-ray result"
        ]
    },
    {
        "category": "Drug",
        "intent": "drug_question",
        "queries": [
            "Is it safe to combine lisinopril and spironolactone?",
            "What are the severe side effects of metformin?",
            "Identify major drug interactions with blood thinners like warfarin",
            "What is the recommended daily dosage for ibuprofen?"
        ]
    },
    {
        "category": "Doctor Search",
        "intent": "doctor_recommendation",
        "queries": [
            "Search pediatrician cardiologist with high rating",
            "Find a dermatologist with over 10 years experience",
            "Recommend a physician specialist for joint pain",
            "Find a clinic surgeon for orthopedic consultation"
        ]
    },
    {
        "category": "Conversation Recall",
        "intent": "conversation_recall",
        "queries": [
            "Retrieve our discussion on blood glucose levels",
            "What did we decide about my daily exercise routine?",
            "Recall details from my last doctor chat history",
            "What did you tell me earlier about dietary recommendations?"
        ]
    },
    {
        "category": "General Healthcare",
        "intent": "general_health",
        "queries": [
            "Suggest a healthy low-sodium diet routine",
            "How can I improve my sleep pattern naturally?",
            "What is a simple fitness routine for weight loss?",
            "What foods are rich in omega-3 fatty acids?"
        ]
    },
    {
        "category": "Unknown Queries",
        "intent": "unknown",
        "queries": [
            "xyzabc123789",
            "random gibberish search index",
            "what is the distance to the moon?",
            "best stock market investments today"
        ]
    }
]


class RAGBenchmarkService:
    """Automated benchmark executor mapping intent categories to evaluation parameters"""

    def __init__(self, evaluation_service: RetrievalEvaluationService):
        self.evaluation_service = evaluation_service

    async def execute_benchmarks(
        self,
        patient_id: Optional[str] = None,
        token_budget: int = 4000,
        score_threshold: float = 0.3
    ) -> Dict[str, Any]:
        """
        Execute full benchmark suite running all test queries across the 7 intents.
        Aggregates query latency, accuracy, and cache utilization.
        """
        start_time = time.perf_counter()
        
        category_results = {}
        all_evaluations = []
        
        total_queries = 0
        total_precision = 0.0
        total_recall = 0.0
        total_latency = 0.0
        total_citations = 0.0
        total_duplicate_rate = 0.0
        total_context_util = 0.0

        for dataset in BENCHMARK_DATASET:
            cat_name = dataset["category"]
            intent = dataset["intent"]
            queries = dataset["queries"]

            cat_latencies = []
            cat_precisions = []
            cat_recalls = []
            cat_citations = []
            
            cat_evals = []

            for q in queries:
                # Running evaluation for this query
                eval_res = await self.evaluation_service.evaluate_query(
                    query=q,
                    patient_id=patient_id,
                    ground_truth_doc_ids=None,  # No predefined ground truths for general bench
                    score_threshold=score_threshold,
                    token_budget=token_budget
                )
                
                metrics = eval_res["metrics"]
                cat_latencies.append(metrics["latency_ms"])
                cat_precisions.append(metrics["precision"])
                cat_recalls.append(metrics["recall"])
                cat_citations.append(metrics["citation_quality"])
                
                all_evaluations.append(eval_res)
                cat_evals.append({
                    "query": q,
                    "latency_ms": metrics["latency_ms"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "citation_quality": metrics["citation_quality"],
                    "duplicate_rate": metrics["duplicate_rate"],
                    "context_utilization": metrics["context_utilization"]
                })

                total_queries += 1
                total_precision += metrics["precision"]
                total_recall += metrics["recall"]
                total_latency += metrics["latency_ms"]
                total_citations += metrics["citation_quality"]
                total_duplicate_rate += metrics["duplicate_rate"]
                total_context_util += metrics["context_utilization"]

            category_results[cat_name] = {
                "intent": intent,
                "avg_latency_ms": sum(cat_latencies) / len(cat_latencies) if cat_latencies else 0.0,
                "avg_precision": sum(cat_precisions) / len(cat_precisions) if cat_precisions else 0.0,
                "avg_recall": sum(cat_recalls) / len(cat_recalls) if cat_recalls else 0.0,
                "avg_citation_quality": sum(cat_citations) / len(cat_citations) if cat_citations else 0.0,
                "query_details": cat_evals
            }

        total_run_time = (time.perf_counter() - start_time) * 1000.0

        # Query metrics summary
        benchmark_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_queries_run": total_queries,
            "total_latency_ms": total_run_time,
            "avg_latency_per_query_ms": total_latency / total_queries if total_queries > 0 else 0.0,
            "avg_precision": total_precision / total_queries if total_queries > 0 else 0.0,
            "avg_recall": total_recall / total_queries if total_queries > 0 else 0.0,
            "avg_citation_quality": total_citations / total_queries if total_queries > 0 else 0.0,
            "avg_duplicate_rate": total_duplicate_rate / total_queries if total_queries > 0 else 0.0,
            "avg_context_utilization": total_context_util / total_queries if total_queries > 0 else 0.0,
            "categories": category_results
        }

        # Persist benchmark execution record to MongoDB
        try:
            db = get_database()
            await db.rag_benchmarks.insert_one(benchmark_report.copy())
        except Exception:
            pass

        # Pop MongoDB object IDs from the copy
        benchmark_report.pop("_id", None)
        return benchmark_report

    async def get_benchmark_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent benchmark suites runs history from MongoDB"""
        try:
            db = get_database()
            cursor = db.rag_benchmarks.find().sort("timestamp", -1).limit(limit)
            history = []
            async for doc in cursor:
                doc.pop("_id", None)
                history.append(doc)
            return history
        except Exception:
            return []


# Singleton dependency helper
_benchmark_service_instance: Optional[RAGBenchmarkService] = None


def get_rag_benchmark_service() -> RAGBenchmarkService:
    """Retrieve singleton instance of RAGBenchmarkService"""
    global _benchmark_service_instance
    if _benchmark_service_instance is None:
        from app.core.dependencies import get_retrieval_evaluation_service
        eval_svc = get_retrieval_evaluation_service()
        _benchmark_service_instance = RAGBenchmarkService(evaluation_service=eval_svc)
    return _benchmark_service_instance
