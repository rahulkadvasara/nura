"""
Nura - Reminders and Notifications Models Tests
Tests for reminders, notifications, and notification preferences Pydantic models
"""

import pytest
from datetime import datetime, timezone
from bson import ObjectId

from app.models.reminder import (
    ReminderType,
    ReminderStatus,
    ReminderSourceType,
    ReminderCreate,
    ReminderUpdate,
    ReminderInDB,
)
from app.models.notification import (
    NotificationType,
    NotificationPriority,
    NotificationCreate,
    NotificationUpdate,
    NotificationInDB,
)
from app.models.preferences import (
    NotificationPreferencesBase,
    NotificationPreferencesUpdate,
    NotificationPreferencesInDB,
    NotificationPreferencesResponse,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TestReminderEnums:
    def test_reminder_type_values(self):
        assert ReminderType.MEDICATION == "medication"
        assert ReminderType.APPOINTMENT == "appointment"
        assert ReminderType.HEALTH_CHECK == "health_check"
        assert ReminderType.CUSTOM == "custom"

    def test_reminder_status_values(self):
        assert ReminderStatus.ACTIVE == "active"
        assert ReminderStatus.COMPLETED == "completed"
        assert ReminderStatus.CANCELLED == "cancelled"

    def test_reminder_source_type_values(self):
        assert ReminderSourceType.PRESCRIPTION == "prescription"
        assert ReminderSourceType.APPOINTMENT == "appointment"
        assert ReminderSourceType.MANUAL == "manual"
        assert ReminderSourceType.AI_GENERATED == "ai_generated"


class TestReminderModel:
    def test_create_reminder(self):
        reminder = ReminderCreate(
            patient_id="507f1f77bcf86cd799439001",
            reminder_type=ReminderType.MEDICATION,
            title="Take Aspirin",
            description="Take one tablet after dinner",
            scheduled_time="20:00",
            recurrence="daily",
            status=ReminderStatus.ACTIVE,
            source_type=ReminderSourceType.PRESCRIPTION,
            source_id="507f1f77bcf86cd799439002",
        )
        assert reminder.patient_id == "507f1f77bcf86cd799439001"
        assert reminder.reminder_type == ReminderType.MEDICATION
        assert reminder.title == "Take Aspirin"
        assert reminder.description == "Take one tablet after dinner"
        assert reminder.scheduled_time == "20:00"
        assert reminder.recurrence == "daily"
        assert reminder.status == ReminderStatus.ACTIVE
        assert reminder.source_type == ReminderSourceType.PRESCRIPTION
        assert reminder.source_id == "507f1f77bcf86cd799439002"

    def test_reminder_default_values(self):
        reminder = ReminderCreate(
            patient_id="patient_1",
            reminder_type=ReminderType.CUSTOM,
            title="Drink water",
            scheduled_time="14:00",
        )
        assert reminder.description is None
        assert reminder.recurrence is None
        assert reminder.status == ReminderStatus.ACTIVE
        assert reminder.source_type == ReminderSourceType.MANUAL
        assert reminder.source_id is None

    def test_reminder_update_partial(self):
        update = ReminderUpdate(status=ReminderStatus.COMPLETED, recurrence="none")
        assert update.status == ReminderStatus.COMPLETED
        assert update.recurrence == "none"
        assert update.title is None

    def test_reminder_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "patient_id": ObjectId("507f1f77bcf86cd799439001"),
            "reminder_type": "medication",
            "title": "Aspirin",
            "scheduled_time": "20:00",
            "status": "active",
            "source_type": "manual",
            "created_at": now,
            "updated_at": now,
        }
        reminder = ReminderInDB.from_mongo(raw)
        assert reminder.id == "507f1f77bcf86cd799439080"
        assert reminder.patient_id == "507f1f77bcf86cd799439001"
        assert reminder.created_at == now
        assert reminder.updated_at == now


class TestNotificationEnums:
    def test_notification_type_values(self):
        assert NotificationType.APPOINTMENT == "appointment"
        assert NotificationType.REMINDER == "reminder"
        assert NotificationType.REPORT == "report"
        assert NotificationType.SYSTEM == "system"
        assert NotificationType.AI_INSIGHT == "ai_insight"

    def test_notification_priority_values(self):
        assert NotificationPriority.LOW == "low"
        assert NotificationPriority.MEDIUM == "medium"
        assert NotificationPriority.HIGH == "high"


class TestNotificationModel:
    def test_create_notification(self):
        notification = NotificationCreate(
            user_id="507f1f77bcf86cd799439001",
            notification_type=NotificationType.APPOINTMENT,
            title="Appointment Confirmed",
            message="Your appointment tomorrow at 10:00 AM has been confirmed.",
            read=False,
            priority=NotificationPriority.HIGH,
            related_entity_type="appointment",
            related_entity_id="507f1f77bcf86cd799439002",
        )
        assert notification.user_id == "507f1f77bcf86cd799439001"
        assert notification.notification_type == NotificationType.APPOINTMENT
        assert notification.title == "Appointment Confirmed"
        assert notification.message == "Your appointment tomorrow at 10:00 AM has been confirmed."
        assert not notification.read
        assert notification.priority == NotificationPriority.HIGH
        assert notification.related_entity_type == "appointment"
        assert notification.related_entity_id == "507f1f77bcf86cd799439002"

    def test_notification_default_values(self):
        notification = NotificationCreate(
            user_id="user_1",
            notification_type=NotificationType.SYSTEM,
            title="Welcome",
            message="Welcome to Nura!",
        )
        assert not notification.read
        assert notification.priority == NotificationPriority.MEDIUM
        assert notification.related_entity_type is None
        assert notification.related_entity_id is None

    def test_notification_update_partial(self):
        update = NotificationUpdate(read=True)
        assert update.read is True
        assert update.title is None

    def test_notification_in_db_from_mongo(self):
        now = utc_now()
        raw = {
            "_id": ObjectId("507f1f77bcf86cd799439080"),
            "user_id": ObjectId("507f1f77bcf86cd799439001"),
            "notification_type": "system",
            "title": "Welcome",
            "message": "Welcome!",
            "read": False,
            "priority": "medium",
            "created_at": now,
        }
        notification = NotificationInDB.from_mongo(raw)
        assert notification.id == "507f1f77bcf86cd799439080"
        assert notification.user_id == "507f1f77bcf86cd799439001"
        assert notification.created_at == now


class TestNotificationPreferencesModel:
    def test_sync_legacy_to_new(self):
        # Pass legacy fields only, verify new fields match
        prefs = NotificationPreferencesBase(
            email_enabled=True,
            appointment_enabled=False,
            reminder_enabled=True,
            report_enabled=False,
            marketing_enabled=True,
        )
        assert prefs.email_notifications is True
        assert prefs.appointment_reminders is False
        assert prefs.medication_reminders is True
        assert prefs.report_updates is False
        assert prefs.marketing_notifications is True

    def test_sync_new_to_legacy(self):
        # Pass new fields only, verify legacy fields match
        prefs = NotificationPreferencesBase(
            email_notifications=False,
            appointment_reminders=True,
            medication_reminders=False,
            report_updates=True,
            marketing_notifications=True,
        )
        assert prefs.email_enabled is False
        assert prefs.appointment_enabled is True
        assert prefs.reminder_enabled is False
        assert prefs.report_enabled is True
        assert prefs.marketing_enabled is True

    def test_sync_update_model(self):
        update = NotificationPreferencesUpdate(
            email_notifications=False,
            appointment_enabled=True,
        )
        # Verify sync keeps both set correctly
        assert update.email_notifications is False
        assert update.email_enabled is False
        assert update.appointment_reminders is True
        assert update.appointment_enabled is True
        assert update.medication_reminders is None
        assert update.reminder_enabled is None
