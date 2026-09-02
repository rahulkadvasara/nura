"""
Nura - Reminder Dispatch Service
Background service for automatically sending scheduled medication reminder emails to patients
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.services.email_service import EmailService

logger = logging.getLogger("nura.services.reminder_dispatch")


class ReminderDispatchService:
    """Background service that periodically checks due reminders and sends email notifications."""

    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None, email_service: Optional[EmailService] = None):
        self.db = db
        self.email_service = email_service or EmailService()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def _get_db(self) -> AsyncIOMotorDatabase:
        if self.db is None:
            self.db = get_database()
        return self.db

    async def start(self):
        """Start the background scheduler loop"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("ReminderDispatchService background worker started.")

    async def stop(self):
        """Stop the background scheduler loop"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("ReminderDispatchService background worker stopped.")

    async def _loop(self):
        """Main loop executing every 30 seconds"""
        while self._running:
            try:
                await self.run_dispatch_cycle()
            except Exception as e:
                logger.error(f"Error in ReminderDispatchService execution cycle: {e}")
            await asyncio.sleep(30)

    async def run_dispatch_cycle(self) -> int:
        """Single execution cycle checking due reminders and sending emails"""
        db = self._get_db()
        now = datetime.now()
        
        # 1. Generate comprehensive time representations (24-hr, 12-hr, spaces, casing, unpadded)
        h_24 = str(now.hour)
        m_24 = now.strftime("%M")
        time_24_padded = f"{now.hour:02d}:{m_24}"
        time_24_unpadded = f"{h_24}:{m_24}"
        
        h_12 = now.hour % 12 or 12
        period = "AM" if now.hour < 12 else "PM"
        period_lower = period.lower()
        
        t_12_upper_space = f"{h_12}:{m_24} {period}"
        t_12_lower_space = f"{h_12}:{m_24} {period_lower}"
        t_12_upper_nospace = f"{h_12}:{m_24}{period}"
        t_12_lower_nospace = f"{h_12}:{m_24}{period_lower}"
        t_12_pad_upper_space = f"{h_12:02d}:{m_24} {period}"
        t_12_pad_lower_space = f"{h_12:02d}:{m_24} {period_lower}"

        matching_times = list(dict.fromkeys([
            time_24_padded, time_24_unpadded,
            t_12_upper_space, t_12_lower_space,
            t_12_upper_nospace, t_12_lower_nospace,
            t_12_pad_upper_space, t_12_pad_lower_space
        ]))
        
        current_minute_tag = now.strftime("%Y-%m-%d %H:%M")

        # 2. Query active reminders matching any scheduled time format in either field
        cursor = db.reminders.find({
            "status": "active",
            "$or": [
                {"scheduled_time": {"$in": matching_times}},
                {"time": {"$in": matching_times}}
            ]
        })
        due_reminders = await cursor.to_list(length=200)

        dispatched_count = 0
        for reminder in due_reminders:
            reminder_id = str(reminder.get("_id"))
            last_notified = reminder.get("last_notified_at")
            
            # Prevent double dispatch in the same minute
            if last_notified == current_minute_tag:
                continue

            patient_id = reminder.get("patient_id")
            title = reminder.get("title", "Medication Reminder")
            scheduled_time = reminder.get("scheduled_time") or reminder.get("time") or time_24_padded
            recurrence = reminder.get("recurrence", "daily")
            description = reminder.get("description", "")

            # Look up patient user record to get registered email address
            patient_email = None
            patient_name = "Patient"

            # Check users collection
            try:
                from bson import ObjectId
                user_doc = None
                if patient_id:
                    if ObjectId.is_valid(patient_id):
                        user_doc = await db.users.find_one({"_id": ObjectId(patient_id)})
                    if not user_doc:
                        user_doc = await db.users.find_one({"id": patient_id})
                    if not user_doc:
                        user_doc = await db.users.find_one({"patient_id": patient_id})

                if user_doc:
                    patient_email = user_doc.get("email")
                    patient_name = user_doc.get("full_name") or user_doc.get("name") or "Patient"
            except Exception as u_err:
                logger.warning(f"Failed to lookup patient user record for reminder {reminder_id}: {u_err}")

            if not patient_email:
                logger.warning(f"Cannot send reminder email for reminder '{title}' (ID {reminder_id}): No email found for patient {patient_id}")
                # Mark as processed for this minute so we don't spam warnings
                await db.reminders.update_one({"_id": reminder["_id"]}, {"$set": {"last_notified_at": current_minute_tag}})
                continue

            # Send reminder email
            sent_success = await self.email_service.send_reminder_email(
                to_email=patient_email,
                patient_name=patient_name,
                reminder_title=title,
                scheduled_time=scheduled_time,
                recurrence=recurrence,
                description=description
            )

            if sent_success:
                dispatched_count += 1
                logger.info(f"Successfully dispatched medication reminder email '{title}' to {patient_email}")

            # Record dispatch timestamp to prevent duplicate notifications
            await db.reminders.update_one(
                {"_id": reminder["_id"]},
                {"$set": {"last_notified_at": current_minute_tag, "updated_at": datetime.utcnow()}}
            )

        return dispatched_count


_reminder_dispatch_service: Optional[ReminderDispatchService] = None

def get_reminder_dispatch_service() -> ReminderDispatchService:
    global _reminder_dispatch_service
    if _reminder_dispatch_service is None:
        _reminder_dispatch_service = ReminderDispatchService()
    return _reminder_dispatch_service
