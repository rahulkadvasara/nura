"""
Nura - Appointment Service
Business logic and validation for appointments
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Any

from app.models.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentStatus,
    PaymentStatus,
)
from app.schemas.appointment import (
    AppointmentCreateSchema,
    AppointmentUpdateSchema,
    AppointmentResponse,
)
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _appointment_to_response(appointment: AppointmentInDB) -> AppointmentResponse:
    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        availability_id=appointment.availability_id,
        slot_date=appointment.slot_date,
        slot_time=appointment.slot_time,
        duration_minutes=appointment.duration_minutes,
        consultation_fee=appointment.consultation_fee,
        status=appointment.status,
        payment_status=appointment.payment_status,
        reason=appointment.reason,
        notes=appointment.notes,
        rejection_reason=appointment.rejection_reason,
        consultation_started_at=appointment.consultation_started_at,
        consultation_completed_at=appointment.consultation_completed_at,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
    )


class AppointmentService(BaseService[AppointmentInDB, AppointmentCreate, AppointmentUpdate]):
    """Service layer for appointment operations"""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        doctor_profile_repository: DoctorProfileRepository,
        user_repository: UserRepository,
        doctor_availability_repository: Optional[Any] = None,
    ):
        super().__init__()
        self.appointment_repository = appointment_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.user_repository = user_repository
        self.doctor_availability_repository = doctor_availability_repository

    async def create_appointment(
        self,
        patient_id: str,
        schema: AppointmentCreateSchema,
    ) -> AppointmentInDB:
        """Create a new appointment request after performing strict booking validation rules"""
        # Validate patient exists
        patient = await self.user_repository.get(patient_id)
        if not patient:
            raise ValueError(f"Patient user with ID {patient_id} does not exist")

        # Validate doctor exists
        doctor = await self.doctor_profile_repository.get(schema.doctor_id)
        if not doctor:
            raise ValueError(f"Doctor profile with ID {schema.doctor_id} does not exist")

        # Validate doctor is verified
        from app.models.doctor import DoctorProfileStatus
        if doctor.profile_status != DoctorProfileStatus.VERIFIED:
            raise ValueError("Doctor profile is not verified")

        # Validate own doctor account booking block
        if patient_id == doctor.user_id:
            raise ValueError("You cannot book an appointment with your own doctor profile")

        # Fetch and validate availability slot
        if not self.doctor_availability_repository:
            from app.db.mongodb import get_database
            from app.repositories.doctor_repository import DoctorAvailabilityRepository
            db = get_database()
            self.doctor_availability_repository = DoctorAvailabilityRepository(db.doctor_availability)

        slot = await self.doctor_availability_repository.get(schema.availability_id)
        if not slot:
            raise ValueError(f"Availability slot with ID {schema.availability_id} does not exist")

        # Validate slot is active and available
        if not slot.active or not slot.is_available:
            raise ValueError("This slot is not available for booking")

        # Validate slot belongs to the requested doctor
        if slot.doctor_id != schema.doctor_id:
            raise ValueError("This availability slot does not belong to the specified doctor")

        # Validate slot is not expired (using IST timezone comparison)
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        current_date_str = ist_now.strftime("%Y-%m-%d")
        current_time_str = ist_now.strftime("%H:%M")
        
        is_future_date = slot.date > current_date_str
        is_future_time = slot.date == current_date_str and slot.end_time >= current_time_str
        if not (is_future_date or is_future_time):
            raise ValueError("Cannot book an expired slot in the past")

        # Prevent double booking same slot by any patient
        existing_any = await self.appointment_repository.get_many({
            "doctor_id": schema.doctor_id,
            "slot_date": slot.date,
            "slot_time": slot.start_time,
            "status": {"$in": [AppointmentStatus.PENDING.value, AppointmentStatus.APPROVED.value, AppointmentStatus.COMPLETED.value]}
        })
        if existing_any:
            raise ValueError("This slot has already been booked or has a pending request")

        # Prevent duplicate pending appointment by the same patient for the same slot
        existing_patient = await self.appointment_repository.get_many({
            "patient_id": patient_id,
            "doctor_id": schema.doctor_id,
            "slot_date": slot.date,
            "slot_time": slot.start_time,
            "status": {"$in": [AppointmentStatus.PENDING.value, AppointmentStatus.APPROVED.value]}
        })
        if existing_patient:
            raise ValueError("You already have a pending or approved appointment request for this slot")

        now = utc_now()
        appointment_create = AppointmentCreate(
            patient_id=patient_id,
            doctor_id=schema.doctor_id,
            availability_id=schema.availability_id,
            slot_date=slot.date,
            slot_time=slot.start_time,
            duration_minutes=slot.slot_duration,
            consultation_fee=doctor.consultation_fee,
            status=AppointmentStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            reason=schema.reason,
            notes=schema.notes,
        )

        doc_dict = appointment_create.model_dump()
        doc_dict["created_at"] = now
        doc_dict["updated_at"] = now

        result = await self.appointment_repository.collection.insert_one(doc_dict)
        created = await self.appointment_repository.collection.find_one({"_id": result.inserted_id})
        if created is None:
            raise RuntimeError("Appointment was inserted but could not be retrieved")
        return AppointmentInDB.from_mongo(created)

    async def get_appointment_by_id(self, appointment_id: str) -> Optional[AppointmentInDB]:
        """Fetch appointment by its ID"""
        return await self.appointment_repository.get(appointment_id)

    async def list_appointments(self, limit: int = 100, skip: int = 0) -> List[AppointmentInDB]:
        """List all appointments"""
        return await self.appointment_repository.list(limit=limit, skip=skip)

    async def list_appointments_by_patient(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AppointmentInDB]:
        """Fetch all appointments for a patient"""
        return await self.appointment_repository.get_by_patient_id(patient_id, limit=limit, skip=skip)

    async def list_appointments_by_doctor(
        self,
        doctor_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[AppointmentInDB]:
        """Fetch all appointments for a doctor"""
        return await self.appointment_repository.get_by_doctor_id(doctor_id, limit=limit, skip=skip)

    async def list_patient_appointments_history(
        self,
        patient_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[dict]:
        """Fetch patient appointment requests with associated doctor user details, sorted newest first"""
        appts = await self.appointment_repository.get_many(
            {"patient_id": patient_id},
            limit=limit,
            skip=skip
        )
        
        # Sort by created_at descending (newest first)
        appts.sort(key=lambda a: a.created_at, reverse=True)

        history = []
        for appt in appts:
            doctor_profile = await self.doctor_profile_repository.get(appt.doctor_id)
            doctor_name = "Unknown Doctor"
            specialization = "General Medicine"
            if doctor_profile:
                specialization = doctor_profile.specialization
                doctor_user = await self.user_repository.get(doctor_profile.user_id)
                if doctor_user:
                    doctor_name = doctor_user.full_name

            history.append({
                "id": appt.id,
                "doctor_id": appt.doctor_id,
                "doctor_name": doctor_name,
                "specialization": specialization,
                "appointment_date": appt.slot_date,
                "appointment_time": appt.slot_time,
                "status": appt.status.value if hasattr(appt.status, "value") else appt.status,
                "payment_status": appt.payment_status.value if hasattr(appt.payment_status, "value") else appt.payment_status,
                "consultation_fee": appt.consultation_fee,
                "reason": appt.reason or appt.notes or "General Consultation",
                "rejection_reason": appt.rejection_reason,
                "created_at": appt.created_at
            })

        return history

    async def cancel_patient_appointment(
        self,
        appointment_id: str,
        patient_id: str,
    ) -> Optional[AppointmentInDB]:
        """Cancel a pending appointment request. Status is updated to cancelled."""
        appt = await self.appointment_repository.get(appointment_id)
        if not appt or appt.patient_id != patient_id:
            raise ValueError("Appointment not found or access denied")

        if appt.status != AppointmentStatus.PENDING:
            raise ValueError(f"Cannot cancel appointment with status: {appt.status.value if hasattr(appt.status, 'value') else appt.status}")

        update = AppointmentUpdate(status=AppointmentStatus.CANCELLED)
        return await self.appointment_repository.update(appointment_id, update)

    async def update_appointment(
        self,
        appointment_id: str,
        schema: AppointmentUpdateSchema,
    ) -> Optional[AppointmentInDB]:
        """Update an existing appointment. If doctor_id is updated, validate it."""
        if schema.doctor_id is not None:
            doctor = await self.doctor_profile_repository.get(schema.doctor_id)
            if not doctor:
                raise ValueError(f"Doctor profile with ID {schema.doctor_id} does not exist")

        update = AppointmentUpdate(**schema.model_dump(exclude_unset=True))
        return await self.appointment_repository.update(appointment_id, update)

    async def delete_appointment(self, appointment_id: str) -> bool:
        """Permanently delete an appointment"""
        return await self.appointment_repository.delete(appointment_id)

    async def list_doctor_appointments(
        self,
        doctor_profile_id: str,
        limit: int = 100,
        skip: int = 0,
    ) -> List[dict]:
        """Fetch doctor appointment queue with patient user details, sorted pending first and newest first"""
        appts = await self.appointment_repository.get_many(
            {"doctor_id": doctor_profile_id},
            limit=limit,
            skip=skip
        )
        
        # Sort by created_at descending (newest first)
        appts.sort(key=lambda a: a.created_at, reverse=True)
        # Stable sort putting pending status first
        appts.sort(key=lambda a: a.status != AppointmentStatus.PENDING)

        queue = []
        for appt in appts:
            patient = await self.user_repository.get(appt.patient_id)
            patient_name = "Unknown Patient"
            if patient:
                patient_name = patient.full_name

            queue.append({
                "id": appt.id,
                "patient_id": appt.patient_id,
                "patient_name": patient_name,
                "appointment_date": appt.slot_date,
                "appointment_time": appt.slot_time,
                "reason": appt.reason or appt.notes or "General Consultation",
                "status": appt.status.value if hasattr(appt.status, "value") else appt.status,
                "rejection_reason": appt.rejection_reason,
                "created_at": appt.created_at
            })

        return queue

    async def approve_appointment(
        self,
        appointment_id: str,
        doctor_profile_id: str,
        doctor_user_id: str,
        notification_service: Any,
        audit_log_service: Any,
    ) -> AppointmentInDB:
        """Approve a pending appointment request and perform audit log / notification side effects"""
        appt = await self.appointment_repository.get(appointment_id)
        if not appt or appt.doctor_id != doctor_profile_id:
            raise ValueError("Appointment not found or access denied")

        if appt.status != AppointmentStatus.PENDING:
            raise ValueError(f"Cannot approve appointment with status: {appt.status.value if hasattr(appt.status, 'value') else appt.status}")

        # Update status
        update = AppointmentUpdate(status=AppointmentStatus.APPROVED)
        updated = await self.appointment_repository.update(appointment_id, update)
        if not updated:
            raise RuntimeError("Failed to update appointment status")

        # Resolve doctor name
        doctor_profile = await self.doctor_profile_repository.get(doctor_profile_id)
        doctor_name = "Doctor"
        if doctor_profile:
            doctor_user = await self.user_repository.get(doctor_profile.user_id)
            if doctor_user:
                doctor_name = doctor_user.full_name
        
        # Send Notification to patient
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            notif_schema = NotificationCreateSchema(
                user_id=appt.patient_id,
                notification_type=NotificationType.APPOINTMENT_APPROVED,
                title="Appointment Approved",
                message=f"Your appointment request with Dr. {doctor_name} has been approved.",
                priority=NotificationPriority.HIGH,
                related_entity_type="appointment",
                related_entity_id=appointment_id,
            )
            await notification_service.create_notification(notif_schema)
        except Exception:
            # Don't fail the transaction if notification fails, but log it
            pass

        # Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="appointment_approved",
                resource_type="appointments",
                resource_id=appointment_id,
                old_value={"status": "pending"},
                new_value={"status": "approved"},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        return updated

    async def reject_appointment(
        self,
        appointment_id: str,
        doctor_profile_id: str,
        doctor_user_id: str,
        rejection_reason: str,
        notification_service: Any,
        audit_log_service: Any,
    ) -> AppointmentInDB:
        """Reject a pending appointment request and perform audit log / notification side effects"""
        appt = await self.appointment_repository.get(appointment_id)
        if not appt or appt.doctor_id != doctor_profile_id:
            raise ValueError("Appointment not found or access denied")

        if appt.status != AppointmentStatus.PENDING:
            raise ValueError(f"Cannot reject appointment with status: {appt.status.value if hasattr(appt.status, 'value') else appt.status}")

        # Update status and rejection reason
        update = AppointmentUpdate(status=AppointmentStatus.REJECTED, rejection_reason=rejection_reason)
        updated = await self.appointment_repository.update(appointment_id, update)
        if not updated:
            raise RuntimeError("Failed to update appointment status")

        # Resolve doctor name
        doctor_profile = await self.doctor_profile_repository.get(doctor_profile_id)
        doctor_name = "Doctor"
        if doctor_profile:
            doctor_user = await self.user_repository.get(doctor_profile.user_id)
            if doctor_user:
                doctor_name = doctor_user.full_name
        
        # Send Notification to patient
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            notif_schema = NotificationCreateSchema(
                user_id=appt.patient_id,
                notification_type=NotificationType.APPOINTMENT_REJECTED,
                title="Appointment Rejected",
                message=f"Your appointment request with Dr. {doctor_name} has been rejected. Reason: {rejection_reason}",
                priority=NotificationPriority.MEDIUM,
                related_entity_type="appointment",
                related_entity_id=appointment_id,
            )
            await notification_service.create_notification(notif_schema)
        except Exception:
            pass

        # Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="appointment_rejected",
                resource_type="appointments",
                resource_id=appointment_id,
                old_value={"status": "pending"},
                new_value={"status": "rejected", "rejection_reason": rejection_reason},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        return updated

    def to_response(self, appointment: AppointmentInDB) -> AppointmentResponse:
        """Convert internal model to API response"""
        return _appointment_to_response(appointment)

    async def start_consultation(
        self,
        appointment_id: str,
        doctor_profile_id: str,
        doctor_user_id: str,
        audit_log_service: Any,
    ) -> AppointmentInDB:
        """Start a consultation for an approved appointment"""
        appt = await self.appointment_repository.get(appointment_id)
        if not appt or appt.doctor_id != doctor_profile_id:
            raise ValueError("Appointment not found or access denied")

        if appt.status != AppointmentStatus.APPROVED:
            raise ValueError(f"Cannot start consultation with status: {appt.status.value if hasattr(appt.status, 'value') else appt.status}")

        now = utc_now()
        update = AppointmentUpdate(status=AppointmentStatus.IN_PROGRESS, consultation_started_at=now)
        updated = await self.appointment_repository.update(appointment_id, update)
        if not updated:
            raise RuntimeError("Failed to start consultation")

        # Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="appointment_started",
                resource_type="appointments",
                resource_id=appointment_id,
                old_value={"status": "approved"},
                new_value={"status": "in_progress", "consultation_started_at": now.isoformat()},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        return updated

    async def complete_consultation(
        self,
        appointment_id: str,
        doctor_profile_id: str,
        doctor_user_id: str,
        schema: Any,  # ConsultationCompleteSchema
        consultation_service: Any,
        notification_service: Any,
        audit_log_service: Any,
    ) -> Any:  # ConsultationInDB
        """Complete a consultation and create the consultation record"""
        appt = await self.appointment_repository.get(appointment_id)
        if not appt or appt.doctor_id != doctor_profile_id:
            raise ValueError("Appointment not found or access denied")

        if appt.status != AppointmentStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete consultation with status: {appt.status.value if hasattr(appt.status, 'value') else appt.status}")

        now = utc_now()
        
        # 1. Create Consultation record
        from app.schemas.appointment import ConsultationCreateSchema
        consult_schema = ConsultationCreateSchema(
            appointment_id=appointment_id,
            patient_id=appt.patient_id,
            doctor_id=doctor_profile_id,
            consultation_notes=schema.notes,
            diagnosis=schema.diagnosis,
            recommendations="", # Default empty string
            follow_up_required=schema.follow_up_required,
            follow_up_date=schema.follow_up_date,
        )
        consultation = await consultation_service.create_consultation(consult_schema)
        
        # 2. Update appointment to completed
        update = AppointmentUpdate(status=AppointmentStatus.COMPLETED, consultation_completed_at=now)
        updated_appt = await self.appointment_repository.update(appointment_id, update)
        if not updated_appt:
            raise RuntimeError("Failed to complete appointment status update")

        # Resolve doctor name for notification
        doctor_name = "Doctor"
        doctor_profile = await self.doctor_profile_repository.get(doctor_profile_id)
        if doctor_profile:
            doctor_user = await self.user_repository.get(doctor_profile.user_id)
            if doctor_user:
                doctor_name = doctor_user.full_name

        # 3. Create Notification for patient
        try:
            from app.schemas.notification import NotificationCreateSchema
            from app.models.notification import NotificationType, NotificationPriority
            notif_schema = NotificationCreateSchema(
                user_id=appt.patient_id,
                notification_type=NotificationType.CONSULTATION_COMPLETED,
                title="Consultation Completed",
                message=f"Your consultation with Dr. {doctor_name} has been completed.",
                priority=NotificationPriority.MEDIUM,
                related_entity_type="consultation",
                related_entity_id=consultation.id,
            )
            await notification_service.create_notification(notif_schema)
        except Exception:
            pass

        # 4. Create Audit Log
        try:
            from app.schemas.observability import AuditLogCreateSchema
            audit_schema = AuditLogCreateSchema(
                user_id=doctor_user_id,
                action="appointment_completed",
                resource_type="appointments",
                resource_id=appointment_id,
                old_value={"status": "in_progress"},
                new_value={"status": "completed", "consultation_completed_at": now.isoformat()},
            )
            await audit_log_service.create_log(audit_schema)
        except Exception:
            pass

        return consultation
