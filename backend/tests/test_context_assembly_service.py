"""
Nura - Unit tests for ContextAssemblyService
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.services.context_assembly_service import ContextAssemblyService, AssembledChunk
from app.schemas.patient_context import PatientContextResponse, PatientContextMetadata
from app.core.ai_config import AISettings
from app.utils.ai import context_assembly_metrics


@pytest.fixture
def mock_patient_context_service():
    service = AsyncMock()
    # Return a mock PatientContextResponse
    metadata = PatientContextMetadata(
        patient_id="pat_123",
        generated_at=datetime.utcnow(),
        sources_used=["patient_memory", "reports", "prescriptions"],
        sections_returned=["patient_profile", "medical_summary", "lab_reports_summary", "prescriptions_summary"],
        estimated_tokens=150,
        context_version="1.0.0"
    )
    
    response = PatientContextResponse(
        patient_profile={"full_name": "John Doe", "email": "john@example.com", "phone": "123-456-7890"},
        medical_summary="Chronic patient diagnosed with hypertension.",
        lifestyle_notes="Drinks occasionally, non-smoker.",
        risk_factors=["High blood pressure"],
        emergency_information="Critical: Monitor blood pressure hourly.",
        current_conditions=["Hypertension"],
        medication_allergies=["Penicillin"],
        past_medical_history=["Appendectomy in 2018"],
        lab_reports_summary=[
            {
                "id": "rep_1",
                "report_type": "Blood Test",
                "risk_level": "high",
                "ai_summary": "Cholesterol levels are elevated.",
                "created_at": "2026-06-01T10:00:00",
                "processing_status": "completed"
            }
        ],
        prescriptions_summary=[
            {
                "id": "pres_1",
                "doctor_id": "doc_abc",
                "medications": [
                    {"drug_name": "Lisinopril", "dosage": "10mg", "frequency": "Daily", "duration": "30 days", "instructions": "Take in morning"}
                ],
                "notes": "Follow up in 1 month.",
                "created_at": "2026-06-05T09:00:00"
            }
        ],
        metadata=metadata
    )
    service.assemble_context.return_value = response
    return service


@pytest.fixture
def mock_retrieval_service():
    service = AsyncMock()
    # Mock return value for retrieve_multiple
    service.retrieve_multiple.return_value = {
        "results": [
            {
                "collection": "patient_reports",
                "id": "chunk_rpt_1",
                "score": 0.9,
                "content": "Patient reports show elevated blood pressure.",
                "metadata": {
                    "document_id": "doc_1",
                    "chunk_id": "chunk_rpt_1",
                    "page_number": 1,
                    "source": "patient_reports",
                    "created_at": "2026-06-01T10:00:00"
                },
                "document_type": "REPORT"
            },
            {
                "collection": "medical_knowledge",
                "id": "chunk_med_1",
                "score": 0.85,
                "content": "Lisinopril is an ACE inhibitor used to treat hypertension.",
                "metadata": {
                    "document_id": "doc_med_1",
                    "chunk_id": "chunk_med_1",
                    "page_number": 3,
                    "source": "medical_knowledge",
                    "created_at": "2025-01-01T00:00:00"
                },
                "document_type": "MEDICAL_ARTICLE"
            },
            {
                "collection": "chat_memory",
                "id": "chunk_chat_1",
                "score": 0.8,
                "content": "User previously asked about drug side effects of Lisinopril.",
                "metadata": {
                    "document_id": "chat_session_1",
                    "chunk_id": "chunk_chat_1",
                    "page_number": 1,
                    "source": "chat_memory",
                    "created_at": "2026-06-25T15:00:00"
                },
                "document_type": "CHAT_MEMORY"
            }
        ],
        "retrieval_time": 15.0,
        "collections_queried": ["patient_reports", "medical_knowledge", "chat_memory"]
    }
    return service


def test_compress_deterministic():
    service = ContextAssemblyService(
        patient_context_service=MagicMock(),
        retrieval_service=MagicMock()
    )

    # Test sentence duplicate removal (case-insensitive and tag-blind)
    text = "Patient exhibits mild symptoms. [Ref 1] Patient exhibits mild symptoms. [Ref 2] PATIENT EXHIBITS MILD SYMPTOMS. Another clean sentence."
    compressed = service.compress(text)
    
    # First sentence and "Another clean sentence" should remain
    assert "Patient exhibits mild symptoms." in compressed
    assert "Another clean sentence." in compressed
    # The duplicate sentence should be removed
    assert compressed.count("Patient exhibits mild symptoms.") == 1


def test_rank_and_citation_generation(mock_retrieval_service, mock_patient_context_service):
    service = ContextAssemblyService(
        patient_context_service=mock_patient_context_service,
        retrieval_service=mock_retrieval_service
    )
    
    # We use ranked sections from mock data
    chunks = mock_retrieval_service.retrieve_multiple.return_value["results"]
    patient_ctx = mock_patient_context_service.assemble_context.return_value.model_dump()
    
    ranked_sections, citation_map = service.rank(chunks, patient_ctx)
    
    # Verify groupings
    assert len(ranked_sections["PATIENT SUMMARY"]) > 0
    assert len(ranked_sections["CURRENT CONDITION"]) > 0
    assert len(ranked_sections["REPORT FINDINGS"]) > 0
    assert len(ranked_sections["MEDICAL KNOWLEDGE"]) > 0
    assert len(ranked_sections["CHAT MEMORY"]) > 0
    
    # Verify citations generated
    assert len(citation_map) == 3
    assert "Ref 1" in citation_map
    assert citation_map["Ref 1"]["document_id"] == "doc_1"
    assert citation_map["Ref 1"]["score"] == 0.9


@pytest.mark.asyncio
async def test_assemble_e2e_successful(mock_patient_context_service, mock_retrieval_service):
    service = ContextAssemblyService(
        patient_context_service=mock_patient_context_service,
        retrieval_service=mock_retrieval_service
    )
    
    context_assembly_metrics.reset()
    
    res = await service.assemble(
        query="hypertension medication",
        patient_id="pat_123",
        token_budget=4000
    )
    
    assert "sections" in res
    assert "citations" in res
    assert "estimated_tokens" in res
    assert "compression_ratio" in res
    
    # Check that sections are present
    assert "PATIENT SUMMARY" in res["sections"]
    assert "CURRENT CONDITION" in res["sections"]
    assert "REPORT FINDINGS" in res["sections"]
    assert "MEDICAL KNOWLEDGE" in res["sections"]
    assert "CHAT MEMORY" in res["sections"]
    
    # Check that citation annotations are present in final text
    report_findings_text = res["sections"]["REPORT FINDINGS"]
    assert "[Ref 1]" in report_findings_text
    
    # Check telemetry metrics
    metrics = context_assembly_metrics.get_metrics()
    assert metrics["assemblies_executed"] == 1
    assert metrics["failed_assemblies"] == 0


@pytest.mark.asyncio
async def test_token_budget_reduction_waterfall(mock_patient_context_service, mock_retrieval_service):
    service = ContextAssemblyService(
        patient_context_service=mock_patient_context_service,
        retrieval_service=mock_retrieval_service
    )
    
    # Set a low token budget to force pruning/waterfall reduction
    # Budget of 150 tokens should force removal of CHAT_MEMORY, MEDICAL_KNOWLEDGE, etc.
    res = await service.assemble(
        query="hypertension",
        patient_id="pat_123",
        token_budget=150
    )
    
    assert res["estimated_tokens"] <= 150
    # Chat memory should have been removed because it is lowest priority
    assert "CHAT MEMORY" not in res["sections"]
    # Patient summary must remain intact
    assert "PATIENT SUMMARY" in res["sections"]
