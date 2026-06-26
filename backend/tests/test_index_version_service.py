"""
Nura - Unit tests for IndexVersionService
"""
import pytest
from app.services.index_version_service import IndexVersionService
from app.core.ai_config import AISettings


def test_index_version_service_defaults():
    settings = AISettings()
    settings.EMBEDDING_VERSION = "v1"
    settings.INDEX_VERSION = 3
    settings.SCHEMA_VERSION = 2

    service = IndexVersionService(settings=settings)
    assert service.get_embedding_version() == "v1"
    assert service.get_index_version() == 3
    assert service.get_schema_version() == 2
    assert service.get_collection_version() == "v1_i3_s2"


def test_index_version_service_compatibility():
    settings = AISettings()
    settings.EMBEDDING_VERSION = "v1"
    settings.INDEX_VERSION = 3
    settings.SCHEMA_VERSION = 2

    service = IndexVersionService(settings=settings)

    # Compatible point
    payload_ok = {
        "embedding_version": "v1",
        "index_version": 3
    }
    assert service.is_compatible(payload_ok) is True

    # Incompatible embedding version
    payload_bad_emb = {
        "embedding_version": "v2",
        "index_version": 3
    }
    assert service.is_compatible(payload_bad_emb) is False

    # Incompatible index version
    payload_bad_idx = {
        "embedding_version": "v1",
        "index_version": 4
    }
    assert service.is_compatible(payload_bad_idx) is False

    # Missing fields
    payload_missing = {
        "index_version": 3
    }
    assert service.is_compatible(payload_missing) is False
