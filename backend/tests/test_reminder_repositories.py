"""
Nura - Reminders and Notifications Repositories Tests
Unit tests for ReminderRepository and NotificationRepository using mocked MongoDB collections.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from bson import ObjectId

from app.models.reminder import (
    ReminderCreate,
    ReminderUpdate,
    ReminderInDB,
    ReminderType,
    ReminderStatus,
    ReminderSourceType,
)
from app.models.notification import (
    NotificationCreate,
    NotificationUpdate,
    NotificationInDB,
    NotificationType,
    NotificationPriority,
)
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.notification_repository import NotificationRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_reminder_doc(
    reminder_id: str = "507f1f77bcf86cd799439080",
    patient_id: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(reminder_id),
        "patient_id": patient_id,
        "reminder_type": "medication",
        "title": "Aspirin",
        "description": "Take after dinner",
        "scheduled_time": "20:00",
        "recurrence": "daily",
        "status": "active",
        "source_type": "manual",
        "source_id": None,
        "created_at": now,
        "updated_at": now,
    }


def make_notification_doc(
    notification_id: str = "507f1f77bcf86cd799439090",
    user_id: str = "507f1f77bcf86cd799439001",
) -> dict:
    now = utc_now()
    return {
        "_id": ObjectId(notification_id),
        "user_id": user_id,
        "notification_type": "system",
        "title": "Welcome",
        "message": "Welcome!",
        "read": False,
        "priority": "medium",
        "related_entity_type": None,
        "related_entity_id": None,
        "created_at": now,
    }


def make_mock_collection(find_one_return=None, find_return=None, update_result=None, update_many_result=None):
    collection = MagicMock()
    collection.find_one = AsyncMock(return_value=find_one_return)

    insert_result = MagicMock()
    insert_result.inserted_id = ObjectId("507f1f77bcf86cd799439080")
    collection.insert_one = AsyncMock(return_value=insert_result)

    upd_result = MagicMock()
    upd_result.modified_count = 1 if update_result is None else update_result
    collection.update_one = AsyncMock(return_value=upd_result)

    upd_many_res = MagicMock()
    upd_many_res.modified_count = 5 if update_many_result is None else update_many_result
    collection.update_many = AsyncMock(return_value=upd_many_res)

    del_result = MagicMock()
    del_result.deleted_count = 1
    collection.delete_one = AsyncMock(return_value=del_result)

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_return or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


class TestReminderRepository:
    @pytest.mark.asyncio
    async def test_create_reminder(self):
        doc = make_reminder_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ReminderRepository(collection)

        reminder_create = ReminderCreate(
            patient_id="507f1f77bcf86cd799439001",
            reminder_type=ReminderType.MEDICATION,
            title="Aspirin",
            scheduled_time="20:00",
        )
        result = await repo.create(reminder_create)
        assert isinstance(result, ReminderInDB)
        assert result.patient_id == "507f1f77bcf86cd799439001"
        assert result.title == "Aspirin"

    @pytest.mark.asyncio
    async def test_get_reminder(self):
        doc = make_reminder_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = ReminderRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439080")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439080"

    @pytest.mark.asyncio
    async def test_get_by_patient_id(self):
        docs = [make_reminder_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ReminderRepository(collection)

        results = await repo.get_by_patient_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].patient_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_get_active_reminders(self):
        docs = [make_reminder_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ReminderRepository(collection)

        results = await repo.get_active_reminders(patient_id="507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].status == ReminderStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_update_reminder(self):
        updated_doc = make_reminder_doc()
        updated_doc["status"] = "completed"
        collection = make_mock_collection(find_one_return=updated_doc)
        repo = ReminderRepository(collection)

        update = ReminderUpdate(status=ReminderStatus.COMPLETED)
        result = await repo.update("507f1f77bcf86cd799439080", update)
        assert result is not None
        assert result.status == ReminderStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_delete_reminder(self):
        collection = make_mock_collection()
        repo = ReminderRepository(collection)
        result = await repo.delete("507f1f77bcf86cd799439080")
        assert result is True

    @pytest.mark.asyncio
    async def test_list_reminders(self):
        docs = [make_reminder_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = ReminderRepository(collection)

        results = await repo.list()
        assert len(results) == 1


class TestNotificationRepository:
    @pytest.mark.asyncio
    async def test_create_notification(self):
        doc = make_notification_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = NotificationRepository(collection)

        notification_create = NotificationCreate(
            user_id="507f1f77bcf86cd799439001",
            notification_type=NotificationType.SYSTEM,
            title="Welcome",
            message="Welcome!",
        )
        result = await repo.create(notification_create)
        assert isinstance(result, NotificationInDB)
        assert result.user_id == "507f1f77bcf86cd799439001"
        assert result.title == "Welcome"

    @pytest.mark.asyncio
    async def test_get_notification(self):
        doc = make_notification_doc()
        collection = make_mock_collection(find_one_return=doc)
        repo = NotificationRepository(collection)

        result = await repo.get_by_id("507f1f77bcf86cd799439090")
        assert result is not None
        assert result.id == "507f1f77bcf86cd799439090"

    @pytest.mark.asyncio
    async def test_get_by_user_id(self):
        docs = [make_notification_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = NotificationRepository(collection)

        results = await repo.get_by_user_id("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert results[0].user_id == "507f1f77bcf86cd799439001"

    @pytest.mark.asyncio
    async def test_get_unread(self):
        docs = [make_notification_doc()]
        collection = make_mock_collection(find_return=docs)
        repo = NotificationRepository(collection)

        results = await repo.get_unread("507f1f77bcf86cd799439001")
        assert len(results) == 1
        assert not results[0].read

    @pytest.mark.asyncio
    async def test_mark_as_read(self):
        doc = make_notification_doc()
        doc["read"] = True
        collection = make_mock_collection(find_one_return=doc)
        repo = NotificationRepository(collection)

        result = await repo.mark_as_read("507f1f77bcf86cd799439090")
        assert result is not None
        assert result.read is True

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self):
        collection = make_mock_collection(update_many_result=3)
        repo = NotificationRepository(collection)

        modified = await repo.mark_all_as_read("507f1f77bcf86cd799439001")
        assert modified == 3
        collection.update_many.assert_called_once_with(
            {"user_id": "507f1f77bcf86cd799439001", "read": False},
            {"$set": {"read": True}}
        )
