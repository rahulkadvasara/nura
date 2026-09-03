"""
End-to-End Test Script for Appointment Flow + Google Meet Integration (Real MongoDB & ENV)
"""
import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from bson import ObjectId

# Load backend/.env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import settings
from app.db.mongodb import connect_to_mongodb, get_database, close_mongodb_connection
from app.repositories import (
    UserRepository,
    DoctorProfileRepository,
    DoctorAvailabilityRepository,
    AppointmentRepository,
    ConsultationRepository,
    NotificationRepository,
    AuditLogRepository,
    SystemIntegrationRepository,
)
from app.services import (
    AppointmentService,
    GoogleMeetService,
    NotificationService,
    AuditLogService,
    ConsultationService,
)
from app.models.user import UserInDB, UserRole, AuthProvider
from app.models.doctor import DoctorProfileInDB, DoctorProfileStatus
from app.models.appointment import AppointmentStatus, PaymentStatus
from app.schemas.appointment import AppointmentCreateSchema, ConsultationCompleteSchema


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


async def run_e2e_test():
    print("==================================================")
    print(" Starting End-to-End Appointment + Google Meet Test")
    print("==================================================")
    print(f"MongoDB URL Configured: {settings.MONGODB_URL[:35]}...")

    # 1. Connect to MongoDB
    await connect_to_mongodb()
    db = get_database()

    user_repo = UserRepository(db.users)
    doc_repo = DoctorProfileRepository(db.doctor_profiles)
    avail_repo = DoctorAvailabilityRepository(db.doctor_availability)
    appt_repo = AppointmentRepository(db.appointments)
    consult_repo = ConsultationRepository(db.consultations)
    notif_repo = NotificationRepository(db.notifications)
    audit_repo = AuditLogRepository(db.audit_logs)
    sys_repo = SystemIntegrationRepository(db.system_integrations)

    # 2. Check stored Google Meet integration token in DB
    meet_token_doc = await sys_repo.get_integration("google_meet")
    print(f"\n[1] Checking stored Google Meet tokens in DB:")
    if meet_token_doc:
        print(f"  -> Found Google Meet integration document in MongoDB!")
        print(f"  -> Refresh token present: {bool(meet_token_doc.get('refresh_token'))}")
        print(f"  -> Access token present:  {bool(meet_token_doc.get('access_token'))}")
        print(f"  -> Token expires at:     {meet_token_doc.get('expires_at')}")
    else:
        print("  -> WARNING: No 'google_meet' document found in system_integrations collection yet.")

    google_meet_service = GoogleMeetService(
        system_integration_repository=sys_repo,
        appointment_repository=appt_repo
    )

    notif_service = NotificationService(notif_repo, user_repo)
    audit_service = AuditLogService(audit_repo, user_repo)
    consult_service = ConsultationService(consult_repo, appt_repo)

    appt_service = AppointmentService(
        appointment_repository=appt_repo,
        doctor_profile_repository=doc_repo,
        user_repository=user_repo,
        doctor_availability_repository=avail_repo,
        google_meet_service=google_meet_service
    )

    # 3. Create Test Patient & Test Doctor
    suffix = str(ObjectId())[-6:]
    patient_email = f"e2e_patient_{suffix}@example.com"
    doctor_email = f"e2e_doctor_{suffix}@example.com"

    now = utc_now()

    patient_id = str(ObjectId())
    patient_doc = {
        "_id": ObjectId(patient_id),
        "id": patient_id,
        "role": UserRole.PATIENT.value,
        "email": patient_email,
        "password_hash": "test_hash",
        "full_name": f"E2E Patient {suffix}",
        "auth_provider": AuthProvider.LOCAL.value,
        "email_verified": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    await user_repo.collection.insert_one(patient_doc)

    doctor_user_id = str(ObjectId())
    doctor_user_doc = {
        "_id": ObjectId(doctor_user_id),
        "id": doctor_user_id,
        "role": UserRole.DOCTOR.value,
        "email": doctor_email,
        "password_hash": "test_hash",
        "full_name": f"Dr. E2E {suffix}",
        "auth_provider": AuthProvider.LOCAL.value,
        "email_verified": True,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    await user_repo.collection.insert_one(doctor_user_doc)

    doctor_profile_id = str(ObjectId())
    doctor_profile_doc = {
        "_id": ObjectId(doctor_profile_id),
        "id": doctor_profile_id,
        "user_id": doctor_user_id,
        "specialization": "General Medicine",
        "experience_years": 8,
        "consultation_fee": 600.0,
        "languages": ["English", "Hindi"],
        "profile_status": DoctorProfileStatus.VERIFIED.value,
        "average_rating": 5.0,
        "total_reviews": 1,
        "created_at": now,
        "updated_at": now,
    }
    await doc_repo.collection.insert_one(doctor_profile_doc)

    # 4. Create Availability Slot (Tomorrow)
    future_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    slot_id = str(ObjectId())
    slot_doc = {
        "_id": ObjectId(slot_id),
        "id": slot_id,
        "doctor_id": doctor_profile_id,
        "date": future_date,
        "start_time": "14:00",
        "end_time": "14:30",
        "slot_duration": 30,
        "is_available": True,
        "active": True,
        "created_at": now,
        "updated_at": now,
    }
    await avail_repo.collection.insert_one(slot_doc)

    print(f"\n[2] Created Test Accounts & Slot:")
    print(f"  -> Patient: {patient_doc['full_name']} (ID: {patient_id})")
    print(f"  -> Doctor:  {doctor_user_doc['full_name']} (Profile ID: {doctor_profile_id})")
    print(f"  -> Slot:    {future_date} 14:00 - 14:30 (Slot ID: {slot_id})")

    # 5. Patient Books Appointment
    booking_schema = AppointmentCreateSchema(
        doctor_id=doctor_profile_id,
        availability_id=slot_id,
        reason="General Health Consultation",
        notes="Testing end-to-end appointment flow with Google Meet",
    )
    created_appt = await appt_service.create_appointment(patient_id, booking_schema)
    print(f"\n[3] Patient Booked Appointment:")
    print(f"  -> Appointment ID: {created_appt.id}")
    print(f"  -> Status:         {created_appt.status.value}")
    print(f"  -> Payment Status: {created_appt.payment_status.value}")

    # 6. Doctor Approves Appointment (Triggering Real Google Meet Creation API Call)
    print(f"\n[4] Doctor Approving Appointment (Triggering real Google Meet generation)...")
    approved_appt = await appt_service.approve_appointment(
        appointment_id=created_appt.id,
        doctor_profile_id=doctor_profile_id,
        doctor_user_id=doctor_user_id,
        notification_service=notif_service,
        audit_log_service=audit_service,
    )

    print(f"  -> Appointment Approved Status: {approved_appt.status.value}")
    print(f"  -> Meeting Link:     {approved_appt.meeting_link}")
    print(f"  -> Meeting Provider: {approved_appt.meeting_provider}")
    print(f"  -> Meeting Created:  {approved_appt.meeting_created_at}")

    # 7. Check Patient History & Doctor Queue API Responses
    patient_history = await appt_service.list_patient_appointments_history(patient_id)
    doctor_queue = await appt_service.list_doctor_appointments(doctor_profile_id)

    print(f"\n[5] Verifying API Responses for Patient & Doctor Views:")
    print(f"  -> Patient History Item meeting_link: {patient_history[0].get('meeting_link') if patient_history else 'None'}")
    print(f"  -> Doctor Queue Item meeting_link:    {doctor_queue[0].get('meeting_link') if doctor_queue else 'None'}")

    # 8. Doctor Starts Consultation
    print(f"\n[6] Doctor Starting Consultation...")
    in_progress_appt = await appt_service.start_consultation(
        appointment_id=created_appt.id,
        doctor_profile_id=doctor_profile_id,
        doctor_user_id=doctor_user_id,
        audit_log_service=audit_service,
    )
    print(f"  -> Status: {in_progress_appt.status.value}")
    print(f"  -> Consultation Started At: {in_progress_appt.consultation_started_at}")

    # 9. Doctor Completes Consultation
    print(f"\n[7] Doctor Completing Consultation...")
    complete_schema = ConsultationCompleteSchema(
        diagnosis="Healthy Checkup",
        notes="Patient is in good health.",
        follow_up_required=False,
    )
    consultation = await appt_service.complete_consultation(
        appointment_id=created_appt.id,
        doctor_profile_id=doctor_profile_id,
        doctor_user_id=doctor_user_id,
        schema=complete_schema,
        consultation_service=consult_service,
        notification_service=notif_service,
        audit_log_service=audit_service,
    )
    print(f"  -> Consultation ID: {consultation.id}")
    print(f"  -> Diagnosis:       {consultation.diagnosis}")

    final_appt = await appt_service.get_appointment_by_id(created_appt.id)
    print(f"  -> Final Appointment Status: {final_appt.status.value}")

    # 10. Clean up test data
    await user_repo.collection.delete_one({"_id": ObjectId(patient_id)})
    await user_repo.collection.delete_one({"_id": ObjectId(doctor_user_id)})
    await doc_repo.collection.delete_one({"_id": ObjectId(doctor_profile_id)})
    await avail_repo.collection.delete_one({"_id": ObjectId(slot_id)})
    await appt_repo.collection.delete_one({"_id": ObjectId(created_appt.id)})
    await consult_repo.collection.delete_one({"_id": ObjectId(consultation.id)})
    print("\n[8] Cleaned up temporary test data from MongoDB.")

    await close_mongodb_connection()
    print("\n==================================================")
    print(" End-to-End Test Completed Successfully!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
