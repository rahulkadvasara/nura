from datetime import date
from typing import Any

from app.schemas.dashboard import DoctorDashboardResponse
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.doctor_wallet_repository import DoctorWalletRepository
from app.repositories.doctor_repository import DoctorProfileRepository, DoctorDocumentRepository
from app.repositories.prescription_repository import PrescriptionRepository


def _today_iso() -> str:
    """Return today's date as YYYY-MM-DD string."""
    return date.today().isoformat()


class DoctorDashboardService:
    """Aggregation service for the doctor dashboard"""

    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        doctor_wallet_repository: DoctorWalletRepository,
        doctor_profile_repository: DoctorProfileRepository,
        doctor_document_repository: DoctorDocumentRepository,
        prescription_repository: PrescriptionRepository,
    ):
        self.appointment_repository = appointment_repository
        self.doctor_wallet_repository = doctor_wallet_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.doctor_document_repository = doctor_document_repository
        self.prescription_repository = prescription_repository

    async def get_dashboard(self, doctor_id: str) -> DoctorDashboardResponse:
        """Aggregate all doctor dashboard data for the given doctor_id."""

        today = _today_iso()

        # 1. Today's appointments (any status, slot_date == today)
        todays_appointments_count = await self.appointment_repository.collection.count_documents({
            "doctor_id": doctor_id,
            "slot_date": today,
        })

        # 2. Upcoming appointments (pending or approved, slot_date > today)
        upcoming_appointments_count = await self.appointment_repository.collection.count_documents({
            "doctor_id": doctor_id,
            "status": {"$in": ["pending", "approved"]},
            "slot_date": {"$gt": today},
        })

        # 3. Total unique patients (distinct patient_ids across all appointments)
        distinct_patient_ids = await self.appointment_repository.collection.distinct(
            "patient_id",
            {"doctor_id": doctor_id},
        )
        total_patients_count = len(distinct_patient_ids)

        # 4. Pending approvals (appointments waiting for doctor action)
        pending_approvals_count = await self.appointment_repository.collection.count_documents({
            "doctor_id": doctor_id,
            "status": "pending",
        })

        # 5. Wallet balance and total earnings from doctor_wallets
        wallet_balance = 0.0
        total_earnings = 0.0
        pending_balance = 0.0
        wallet_doc = await self.doctor_wallet_repository.collection.find_one(
            {"doctor_id": doctor_id}
        )
        if wallet_doc:
            wallet_balance = float(wallet_doc.get("available_balance", 0.0))
            total_earnings = float(wallet_doc.get("total_earned", 0.0))
            pending_balance = float(wallet_doc.get("pending_balance", 0.0))


        # 6. Profile status and document status
        profile_status = "pending"
        document_status = "pending"
        prescriptions_written_count = 0
        
        doctor_profile = await self.doctor_profile_repository.get_by_user_id(doctor_id)
        if doctor_profile:
            profile_status = doctor_profile.profile_status.value
            
            # Fetch documents using profile id
            documents = await self.doctor_document_repository.get_by_doctor_id(doctor_profile.id)
            if documents:
                if any(doc.verification_status.value == "rejected" for doc in documents):
                    document_status = "rejected"
                elif all(doc.verification_status.value == "approved" for doc in documents):
                    document_status = "approved"
                else:
                    document_status = "pending"

            # 7. Count prescriptions written matching the doctor profile ID
            prescriptions_written_count = await self.prescription_repository.collection.count_documents(
                {"doctor_id": doctor_profile.id}
            )

        return DoctorDashboardResponse(
            todays_appointments_count=todays_appointments_count,
            upcoming_appointments_count=upcoming_appointments_count,
            total_patients_count=total_patients_count,
            pending_approvals_count=pending_approvals_count,
            wallet_balance=wallet_balance,
            total_earnings=total_earnings,
            pending_balance=pending_balance,
            profile_status=profile_status,
            document_status=document_status,
            prescriptions_written_count=prescriptions_written_count,
        )


