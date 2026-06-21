"""
Nura - Reminders and Notifications Services Tests
Unit tests for ReminderService and NotificationService using mocked repositories.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.reminder import ReminderInDB, ReminderType, ReminderStatus, ReminderSourceType
from app.models.notification import NotificationInDB, NotificationType, NotificationPriority
from app.models.user import UserInDB, UserRole, AuthProvider
from app.schemas.reminder import ReminderCreateSchema, ReminderUpdateSchema, ReminderResponse
from app.schemas.notification import NotificationCreateSchema, NotificationUpdateSchema, NotificationResponse
from app.services.reminder_service import ReminderService
from app.services.notification_service import NotificationService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def sample_user():
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
def sample_reminder():
    return ReminderInDB(
        id="507f1f77bcf86cd799439080",
        patient_id="507f1f77bcf86cd799439001",
        reminder_type=ReminderType.MEDICATION,
        title="Take Medication",
        description="Daily pills",
        scheduled_time="08:00",
        recurrence="daily",
        status=ReminderStatus.ACTIVE,
        source_type=ReminderSourceType.MANUAL,
        source_id=None,
        created_at=utc_now(),
        updated_at=utc_now(),
    )


@pytest.fixture
def sample_notification():
    return NotificationInDB(
        id="507f1f77bcf86cd799439090",
        user_id="507f1f77bcf86cd799439001",
        notification_type=NotificationType.SYSTEM,
        title="Test Notification",
        message="This is a test notification message",
        read=False,
        priority=NotificationPriority.MEDIUM,
        related_entity_type=None,
        related_entity_id=None,
        created_at=utc_now(),
    )


class TestReminderService:
    @pytest.mark.asyncio
    async def test_create_reminder_success(self, sample_user):
        rem_repo = AsyncMock()
        rem_repo.collection = MagicMock()
        rem_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439080"))
        )
        rem_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": sample_user.id,
            "reminder_type": "medication",
            "title": "Aspirin",
            "description": "Take one tablet",
            "scheduled_time": "20:00",
            "recurrence": "daily",
            "status": "active",
            "source_type": "manual",
            "source_id": None,
            "created_at": utc_now(),
            "updated_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        service = ReminderService(rem_repo, user_repo)
        schema = ReminderCreateSchema(
            patient_id=sample_user.id,
            reminder_type=ReminderType.MEDICATION,
            title="Aspirin",
            description="Take one tablet",
            scheduled_time="20:00",
            recurrence="daily",
        )

        result = await service.create_reminder(schema)
        assert isinstance(result, ReminderInDB)
        assert result.id == "507f1f77bcf86cd799439080"
        user_repo.get.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_create_reminder_patient_not_found(self):
        rem_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = ReminderService(rem_repo, user_repo)
        schema = ReminderCreateSchema(
            patient_id="invalid_patient",
            reminder_type=ReminderType.MEDICATION,
            title="Aspirin",
            scheduled_time="20:00",
        )

        with pytest.raises(ValueError, match="Patient user with ID.*does not exist"):
            await service.create_reminder(schema)

    @pytest.mark.asyncio
    async def test_get_reminder_by_id(self, sample_reminder):
        rem_repo = AsyncMock()
        rem_repo.get = AsyncMock(return_value=sample_reminder)
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        result = await service.get_reminder_by_id(sample_reminder.id)
        assert result == sample_reminder
        rem_repo.get.assert_called_once_with(sample_reminder.id)

    @pytest.mark.asyncio
    async def test_list_reminders(self, sample_reminder):
        rem_repo = AsyncMock()
        rem_repo.list = AsyncMock(return_value=[sample_reminder])
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        result = await service.list_reminders()
        assert len(result) == 1
        assert result[0] == sample_reminder

    @pytest.mark.asyncio
    async def test_list_reminders_by_patient(self, sample_reminder):
        rem_repo = AsyncMock()
        rem_repo.get_by_patient_id = AsyncMock(return_value=[sample_reminder])
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        result = await service.list_reminders_by_patient("patient_1")
        assert len(result) == 1
        rem_repo.get_by_patient_id.assert_called_once_with("patient_1", limit=100, skip=0)

    @pytest.mark.asyncio
    async def test_list_active_reminders(self, sample_reminder):
        rem_repo = AsyncMock()
        rem_repo.get_active_reminders = AsyncMock(return_value=[sample_reminder])
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        result = await service.list_active_reminders("patient_1")
        assert len(result) == 1
        rem_repo.get_active_reminders.assert_called_once_with("patient_1", limit=100, skip=0)

    @pytest.mark.asyncio
    async def test_update_reminder(self, sample_reminder):
        rem_repo = AsyncMock()
        rem_repo.update = AsyncMock(return_value=sample_reminder)
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        schema = ReminderUpdateSchema(title="Updated Title")
        result = await service.update_reminder(sample_reminder.id, schema)
        assert result == sample_reminder
        rem_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_reminder(self):
        rem_repo = AsyncMock()
        rem_repo.delete = AsyncMock(return_value=True)
        user_repo = AsyncMock()

        service = ReminderService(rem_repo, user_repo)
        result = await service.delete_reminder("rem_id")
        assert result is True
        rem_repo.delete.assert_called_once_with("rem_id")

    def test_to_response(self, sample_reminder):
        rem_repo = AsyncMock()
        user_repo = AsyncMock()
        service = ReminderService(rem_repo, user_repo)
        resp = service.to_response(sample_reminder)
        assert isinstance(resp, ReminderResponse)
        assert resp.id == sample_reminder.id
        assert resp.title == sample_reminder.title


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_create_notification_success(self, sample_user):
        not_repo = AsyncMock()
        not_repo.collection = MagicMock()
        not_repo.collection.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439090"))
        )
        not_repo.collection.find_one = AsyncMock(return_value={
            "_id": ObjectId("507f1f77bcf86cd799439090"),
            "user_id": sample_user.id,
            "notification_type": "system",
            "title": "Welcome",
            "message": "Welcome to Nura",
            "read": False,
            "priority": "medium",
            "related_entity_type": None,
            "related_entity_id": None,
            "created_at": utc_now(),
        })

        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=sample_user)

        service = NotificationService(not_repo, user_repo)
        schema = NotificationCreateSchema(
            user_id=sample_user.id,
            notification_type=NotificationType.SYSTEM,
            title="Welcome",
            message="Welcome to Nura",
        )

        result = await service.create_notification(schema)
        assert isinstance(result, NotificationInDB)
        assert result.id == "507f1f77bcf86cd799439090"
        user_repo.get.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_create_notification_user_not_found(self):
        not_repo = AsyncMock()
        user_repo = AsyncMock()
        user_repo.get = AsyncMock(return_value=None)

        service = NotificationService(not_repo, user_repo)
        schema = NotificationCreateSchema(
            user_id="invalid_user",
            notification_type=NotificationType.SYSTEM,
            title="Welcome",
            message="Welcome to Nura",
        )

        with pytest.raises(ValueError, match="User with ID.*does not exist"):
            await service.create_notification(schema)

    @pytest.mark.asyncio
    async def test_get_notification_by_id(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.get = AsyncMock(return_value=sample_notification)
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.get_notification_by_id(sample_notification.id)
        assert result == sample_notification
        not_repo.get.assert_called_once_with(sample_notification.id)

    @pytest.mark.asyncio
    async def test_list_notifications(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.list = AsyncMock(return_value=[sample_notification])
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.list_notifications()
        assert len(result) == 1
        assert result[0] == sample_notification

    @pytest.mark.asyncio
    async def test_list_notifications_by_user(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.get_by_user_id = AsyncMock(return_value=[sample_notification])
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.list_notifications_by_user("user_1")
        assert len(result) == 1
        not_repo.get_by_user_id.assert_called_once_with("user_1", limit=100, skip=0)

    @pytest.mark.asyncio
    async def test_list_unread_notifications(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.get_unread = AsyncMock(return_value=[sample_notification])
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.list_unread_notifications("user_1")
        assert len(result) == 1
        not_repo.get_unread.assert_called_once_with("user_1", limit=100, skip=0)

    @pytest.mark.asyncio
    async def test_mark_notification_as_read(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.mark_as_read = AsyncMock(return_value=sample_notification)
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.mark_notification_as_read(sample_notification.id)
        assert result == sample_notification
        not_repo.mark_as_read.assert_called_once_with(sample_notification.id)

    @pytest.mark.asyncio
    async def test_mark_all_notifications_as_read(self):
        not_repo = AsyncMock()
        not_repo.mark_all_as_read = AsyncMock(return_value=5)
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.mark_all_notifications_as_read("user_1")
        assert result == 5
        not_repo.mark_all_as_read.assert_called_once_with("user_1")

    @pytest.mark.asyncio
    async def test_update_notification(self, sample_notification):
        not_repo = AsyncMock()
        not_repo.update = AsyncMock(return_value=sample_notification)
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        schema = NotificationUpdateSchema(read=True)
        result = await service.update_notification(sample_notification.id, schema)
        assert result == sample_notification
        not_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification(self):
        not_repo = AsyncMock()
        not_repo.delete = AsyncMock(return_value=True)
        user_repo = AsyncMock()

        service = NotificationService(not_repo, user_repo)
        result = await service.delete_notification("not_id")
        assert result is True
        not_repo.delete.assert_called_once_with("not_id")

    def test_to_response(self, sample_notification):
        not_repo = AsyncMock()
        user_repo = AsyncMock()
        service = NotificationService(not_repo, user_repo)
        resp = service.to_response(sample_notification)
        assert isinstance(resp, NotificationResponse)
        assert resp.id == sample_notification.id
        assert resp.title == sample_notification.title
