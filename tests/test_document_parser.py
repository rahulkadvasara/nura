import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.services.report_processing.document_parser import DocumentParser
from app.models.report import ReportInDB, ProcessingStatus, ReportType, RiskLevel


@pytest.mark.asyncio
async def test_document_parser_coordination():
    # Mock Report Repository
    repo = MagicMock()
    repo.collection = MagicMock()
    repo.collection.update_one = AsyncMock(return_value=None)
    repo.collection.find_one = MagicMock(return_value=None)
    
    # Mock Report record
    mock_report = ReportInDB(
        id="test_report_id",
        patient_id="test_patient_id",
        uploaded_by="test_user_id",
        report_type=ReportType.OTHER,
        file_url="uploads/test_file.pdf",
        raw_text=None,
        structured_data=None,
        entities=None,
        ai_summary=None,
        risk_level=RiskLevel.LOW,
        processing_status=ProcessingStatus.UPLOADED,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    repo.get = AsyncMock(return_value=mock_report)
    
    # Mock extractor, preprocessor, and OCR
    extractor = MagicMock()
    extractor.extract_text = AsyncMock(return_value=[
        {"page_number": 1, "text": "Page 1 digital text layout content", "is_scanned": False}
    ])
    
    preprocessor = MagicMock()
    ocr = MagicMock()
    
    parser = DocumentParser(repo, extractor, preprocessor, ocr)
    
    res = await parser.process_report("test_report_id")
    
    # Verify DB update call was made
    repo.collection.update_one.assert_called()
    assert res is not None
