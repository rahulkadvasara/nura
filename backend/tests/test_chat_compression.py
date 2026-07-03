import pytest
from app.models.chat import ChatMessageInDB, MessageRole
from app.services.chat.conversation_compression import ConversationCompressionService
from datetime import datetime, timezone


def create_msg(content: str, role: MessageRole, bookmarked: bool = False, has_citations: bool = False) -> ChatMessageInDB:
    return ChatMessageInDB(
        id=f"msg_{hash(content)}",
        session_id="sess123",
        patient_id="pat123",
        role=role,
        content=content,
        citations=[{"document": "doc1", "source": "src1"}] if has_citations else [],
        attachments=[],
        token_usage={},
        metadata={"bookmarked": True} if bookmarked else {},
        deleted=False,
        created_at=datetime.now(timezone.utc)
    )


@pytest.mark.asyncio
async def test_compression_under_budget():
    service = ConversationCompressionService(max_tokens=100)
    messages = [
        create_msg("Hello", MessageRole.USER),
        create_msg("Hi there", MessageRole.ASSISTANT)
    ]
    history = await service.compress_history(messages)
    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hi there"


@pytest.mark.asyncio
async def test_compression_over_budget_preserves_rules():
    # max_tokens=10 forces compression since 4 messages will exceed it
    service = ConversationCompressionService(max_tokens=10, keep_recent_count=1)
    
    msg_old_normal = create_msg("What is the weather?", MessageRole.USER)
    msg_old_bookmarked = create_msg("Take 500mg Aspirin", MessageRole.USER, bookmarked=True)
    msg_old_cited = create_msg("Here is a source quote", MessageRole.ASSISTANT, has_citations=True)
    msg_old_clinical = create_msg("I have chest pain", MessageRole.USER)
    msg_recent = create_msg("How is it going?", MessageRole.USER)

    messages = [
        msg_old_normal,
        msg_old_bookmarked,
        msg_old_cited,
        msg_old_clinical,
        msg_recent
    ]

    history = await service.compress_history(messages)
    
    # Let's check that normal got compressed and others preserved
    # Output structure: [{"role": "system", "content": "Context summary ..."}, ...]
    assert len(history) > 1
    assert history[0]["role"] == "system"
    assert "What is the weather?" in history[0]["content"]
    
    # Verify bookmarked, cited, clinical, and recent are preserved in the list
    contents = [item["content"] for item in history[1:]]
    assert "Take 500mg Aspirin" in contents
    assert "Here is a source quote" in contents
    assert "I have chest pain" in contents
    assert "How is it going?" in contents
