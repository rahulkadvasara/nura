"""
Nura - Chat and Messaging Services Tests
Unit tests for ChatSessionService and ChatMessageService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.chat import (
    ChatSessionInDB,
    SessionType,
    ChatMessageInDB,
    SenderType,
    MessageType,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.schemas.chat import (
    ChatSessionCreateSchema,
    ChatSessionUpdateSchema,
    ChatSessionResponse,
    ChatMessageCreateSchema,
    ChatMessageUpdateSchema,
    ChatMessageResponse,
    ChatMessageMetadata,
)
from app.services.chat_session_service import ChatSessionService
from app.services.chat_message_service import ChatMessageService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_patient_user():
    return UserInDB(
        id="507f1f77bcf86cd799439001",
        role=UserRole.PATIENT,
        email="patient@example.com",
        password_hash="hashed_pw",
        full_name="Patient Name",
        phone="1234567890",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_doctor_user():
    return UserInDB(
        id="507f1f77bcf86cd799439002",
        role=UserRole.DOCTOR,
        email="doctor@example.com",
        password_hash="hashed_pw",
        full_name="Doctor Name",
        phone="0987654321",
        auth_provider=AuthProvider.LOCAL,
        email_verified=True,
        is_active=True,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_doctor_profile():
    return DoctorProfileInDB(
        id="507f1f77bcf86cd799439003",
        user_id="507f1f77bcf86cd799439002",
        specialization="General Medicine",
        qualifications=["MD"],
        experience_years=5,
        consultation_fee=300.0,
        bio="General doctor.",
        languages=["English"],
        hospital="Clinic A",
        license_number="LIC-123",
        profile_status=DoctorProfileStatus.PENDING,
        average_rating=0.0,
        total_reviews=0,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_chat_session():
    return ChatSessionInDB(
        id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        title="Checkup",
        session_type=SessionType.AI_CHAT,
        active=True,
        last_message_at=utc_now(),
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_chat_message():
    return ChatMessageInDB(
        id="507f1f77bcf86cd799439090",
        session_id="507f1f77bcf86cd799439080",
        sender_type=SenderType.PATIENT,
        sender_id="507f1f77bcf86cd799439001",
        message="Hello",
        message_type=MessageType.TEXT,
        metadata={},
        created_at=utc_now(),
    )


class TestChatSessionService:
    @pytest.mark.asyncio
    async def test_create_session_success(self, sample_patient_user):
        sess_repo = AsyncMock()
        sess_repo.collection = MagicMock()
        sess_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        sess_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": sample_patient_user.id,
            "title": "Discussion",
            "session_type": "ai_chat",
            "active": True,
            "last_message_at": utc_now(),
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_patient_user)

        service = ChatSessionService(sess_repo, user_repo)
        schema = ChatSessionCreateSchema(
            patient_id=sample_patient_user.id,
            title="Discussion",
            session_type=SessionType.AI_CHAT,
        )

        result = await service.create_session(schema)
        assert isinstance(result, ChatSessionInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        user_repo.get.assert_called_once_with(sample_patient_user.id)

    @pytest.mark.asyncio
    async def test_create_session_patient_not_found(self):
        sess_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = ChatSessionService(sess_repo, user_repo)
        schema = ChatSessionCreateSchema(
            patient_id="invalid_patient",
            title="Discussion",
            session_type=SessionType.AI_CHAT,
        )

        with pytest.raises(ValueError, match="Patient user with ID.*does not exist"):
            await service.create_session(schema)

    @pytest.mark.asyncio
    async def test_create_session_not_patient_role(self, sample_doctor_user):
        sess_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_doctor_user)

        service = ChatSessionService(sess_repo, user_repo)
        schema = ChatSessionCreateSchema(
            patient_id=sample_doctor_user.id,
            title="Discussion",
            session_type=SessionType.AI_CHAT,
        )

        with pytest.raises(ValueError, match="is not a patient"):
            await service.create_session(schema)


class TestChatMessageService:
    @pytest.mark.asyncio
    async def test_create_message_patient_success(self, sample_patient_user, sample_chat_session):
        msg_repo = AsyncMock()
        msg_repo.collection = MagicMock()
        msg_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        msg_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "session_id": sample_chat_session.id,
            "sender_type": "patient",
            "sender_id": sample_patient_user.id,
            "message": "Hello doc",
            "message_type": "text",
            "metadata": {},
            "created_at": utc_now(),
        })

        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=sample_chat_session)
        sess_repo.update = AsyncMock()

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_patient_user)

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageCreateSchema(
            session_id=sample_chat_session.id,
            sender_type=SenderType.PATIENT,
            sender_id=sample_patient_user.id,
            message="Hello doc",
        )

        result = await service.create_message(schema)
        assert isinstance(result, ChatMessageInDB)
        assert result.id == "507f1f77bcf86cd799439090"
        sess_repo.get.assert_called_once_with(sample_chat_session.id)
        user_repo.get.assert_called_once_with(sample_patient_user.id)
        sess_repo.update.assert_called_once() # Checks that last_message_at is updated

    @pytest.mark.asyncio
    async def test_create_message_doctor_user_success(self, sample_doctor_user, sample_chat_session):
        msg_repo = AsyncMock()
        msg_repo.collection = MagicMock()
        msg_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        msg_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "session_id": sample_chat_session.id,
            "sender_type": "doctor",
            "sender_id": sample_doctor_user.id,
            "message": "Hello patient",
            "message_type": "text",
            "metadata": {},
            "created_at": utc_now(),
        })

        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=sample_chat_session)
        sess_repo.update = AsyncMock()

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_doctor_user)

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageCreateSchema(
            session_id=sample_chat_session.id,
            sender_type=SenderType.DOCTOR,
            sender_id=sample_doctor_user.id,
            message="Hello patient",
        )

        result = await service.create_message(schema)
        assert result.id == "507f1f77bcf86cd799439090"

    @pytest.mark.asyncio
    async def test_create_message_doctor_profile_success(self, sample_doctor_profile, sample_chat_session):
        msg_repo = AsyncMock()
        msg_repo.collection = MagicMock()
        msg_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        msg_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "session_id": sample_chat_session.id,
            "sender_type": "doctor",
            "sender_id": sample_doctor_profile.id,
            "message": "Hello patient",
            "message_type": "text",
            "metadata": {},
            "created_at": utc_now(),
        })

        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=sample_chat_session)
        sess_repo.update = AsyncMock()

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None) # Try user first, none found

        doc_profile_repo = AsyncMock()
        doc_profile_repo.get = AsyncMock(return_value=sample_doctor_profile)

        service = ChatMessageService(msg_repo, sess_repo, user_repo, doc_profile_repo)
        schema = ChatMessageCreateSchema(
            session_id=sample_chat_session.id,
            sender_type=SenderType.DOCTOR,
            sender_id=sample_doctor_profile.id,
            message="Hello patient",
        )

        result = await service.create_message(schema)
        assert result.id == "507f1f77bcf86cd799439090"
        doc_profile_repo.get.assert_called_once_with(sample_doctor_profile.id)

    @pytest.mark.asyncio
    async def test_create_message_session_not_found(self):
        msg_repo = AsyncMock()
        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=None)
        user_repo = AsyncMock()

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageCreateSchema(
            session_id="invalid_session",
            sender_type=SenderType.PATIENT,
            sender_id="patient_1",
            message="Hello",
        )

        with pytest.raises(ValueError, match="Chat session with ID.*does not exist"):
            await service.create_message(schema)

    @pytest.mark.asyncio
    async def test_create_message_patient_not_found(self, sample_chat_session):
        msg_repo = AsyncMock()
        sess_repo = AsyncMock()
        sess_repo.get = AsyncMock(return_value=sample_chat_session)
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = ChatMessageService(msg_repo, sess_repo, user_repo)
        schema = ChatMessageCreateSchema(
            session_id=sample_chat_session.id,
            sender_type=SenderType.PATIENT,
            sender_id="invalid_patient",
            message="Hello",
        )

        with pytest.raises(ValueError, match="Patient user with ID.*does not exist"):
            await service.create_message(schema)
