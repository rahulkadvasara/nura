"""
Nura - Doctor Patient Service
Business logic and validation for doctor-specific patient management.
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from typing import List, Optional, Tuple, Dict, Any

from app.models.user import UserInDB, UserRole, UserResponse
from app.repositories.user_repository import UserRepository
from app.repositories.doctor_repository import DoctorProfileRepository
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.prescription_repository import PrescriptionRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.health_insight_repository import HealthInsightRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.chat_session_repository import ChatSessionRepository

from app.schemas.doctor_patient import DoctorPatientSummary, DoctorPatientListResponse, DoctorPatientDetailResponse
from app.schemas.appointment import AppointmentResponse, ConsultationResponse, PrescriptionResponse
from app.schemas.report import ReportResponse, HealthInsightResponse
from app.schemas.reminder import ReminderResponse
from app.schemas.chat import ChatSessionResponse

logger = logging.getLogger(__name__)


class DoctorPatientService:
    """Service layer for doctor-specific patient directory operations"""

    def __init__(
        self,
        user_repository: UserRepository,
        doctor_profile_repository: DoctorProfileRepository,
        appointment_repository: AppointmentRepository,
        consultation_repository: ConsultationRepository,
        prescription_repository: PrescriptionRepository,
        report_repository: ReportRepository,
        health_insight_repository: HealthInsightRepository,
        reminder_repository: ReminderRepository,
        chat_session_repository: ChatSessionRepository,
    ):
        self.user_repository = user_repository
        self.doctor_profile_repository = doctor_profile_repository
        self.appointment_repository = appointment_repository
        self.consultation_repository = consultation_repository
        self.prescription_repository = prescription_repository
        self.report_repository = report_repository
        self.health_insight_repository = health_insight_repository
        self.reminder_repository = reminder_repository
        self.chat_session_repository = chat_session_repository

    async def get_patients(
        self,
        doctor_profile_id: str,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> Tuple[List[DoctorPatientSummary], int]:
        """Fetch and aggregate the directory list of patients treated by the doctor"""
        
        # 1. Fetch distinct patient IDs associated with this doctor profile ID
        distinct_patient_ids_appt = await self.appointment_repository.collection.distinct(
            "patient_id",
            {"doctor_id": doctor_profile_id}
        )
        distinct_patient_ids_cons = await self.consultation_repository.collection.distinct(
            "patient_id",
            {"doctor_id": doctor_profile_id}
        )
        patient_ids = list(set(distinct_patient_ids_appt + distinct_patient_ids_cons))

        if not patient_ids:
            return [], 0

        # 2. Build query to retrieve user records
        valid_object_ids = []
        for pid in patient_ids:
            if ObjectId.is_valid(pid):
                valid_object_ids.append(ObjectId(pid))
                
        query: Dict[str, Any] = {
            "role": UserRole.PATIENT.value,
            "_id": {"$in": valid_object_ids}
        }

        if search:
            search_regex = {"$regex": search, "$options": "i"}
            query["$or"] = [
                {"full_name": search_regex},
                {"email": search_regex}
            ]

        # Fetch matching patient users
        cursor = self.user_repository.collection.find(query)
        matching_users = [UserInDB.from_mongo(doc) for doc in await cursor.to_list(length=10000)]

        # 3. For each patient, aggregate summary metrics
        patients_summaries = []
        for user in matching_users:
            # Fetch latest appointment
            latest_appt_doc = await self.appointment_repository.collection.find_one(
                {"patient_id": user.id, "doctor_id": doctor_profile_id},
                sort=[("slot_date", -1), ("slot_time", -1)]
            )
            latest_appointment = None
            if latest_appt_doc:
                from app.models.appointment import AppointmentInDB
                latest_appointment = AppointmentResponse(**AppointmentInDB.from_mongo(latest_appt_doc).model_dump())

            # Fetch latest consultation
            latest_cons_doc = await self.consultation_repository.collection.find_one(
                {"patient_id": user.id, "doctor_id": doctor_profile_id},
                sort=[("created_at", -1)]
            )
            latest_consultation = None
            if latest_cons_doc:
                from app.models.appointment import ConsultationInDB
                latest_consultation = ConsultationResponse(**ConsultationInDB.from_mongo(latest_cons_doc).model_dump())

            # Fetch totals
            total_appointments = await self.appointment_repository.collection.count_documents(
                {"patient_id": user.id, "doctor_id": doctor_profile_id}
            )
            total_consultations = await self.consultation_repository.collection.count_documents(
                {"patient_id": user.id, "doctor_id": doctor_profile_id}
            )
            total_reports = await self.report_repository.collection.count_documents(
                {"patient_id": user.id}
            )

            # Health risk level (from latest completed report)
            latest_report_doc = await self.report_repository.collection.find_one(
                {"patient_id": user.id, "processing_status": "completed"},
                sort=[("created_at", -1)]
            )
            health_risk_level = None
            if latest_report_doc:
                health_risk_level = latest_report_doc.get("risk_level", "low")

            patients_summaries.append(
                DoctorPatientSummary(
                    patient_id=user.id,
                    name=user.full_name,
                    age=None, # age is not stored in default user schema
                    gender=None, # gender is not stored in default user schema
                    profile_picture=user.profile_picture,
                    latest_appointment=latest_appointment,
                    latest_consultation=latest_consultation,
                    total_appointments=total_appointments,
                    total_consultations=total_consultations,
                    total_reports=total_reports,
                    health_risk_level=health_risk_level,
                )
            )

        # 4. Sort the list
        # Sorting parameters supported: name, -name, latest_visit, -latest_visit
        if sort_by == "name":
            patients_summaries.sort(key=lambda p: p.name.lower())
        elif sort_by == "-name":
            patients_summaries.sort(key=lambda p: p.name.lower(), reverse=True)
        elif sort_by == "latest_visit":
            patients_summaries.sort(key=lambda p: (p.latest_appointment.slot_date, p.latest_appointment.slot_time) if p.latest_appointment else ("", ""))
        else: # Default or "-latest_visit"
            patients_summaries.sort(key=lambda p: (p.latest_appointment.slot_date, p.latest_appointment.slot_time) if p.latest_appointment else ("", ""), reverse=True)

        # 5. Apply pagination
        total_count = len(patients_summaries)
        paginated_patients = patients_summaries[skip : skip + limit]

        return paginated_patients, total_count

    async def get_patient_detail(
        self,
        doctor_profile_id: str,
        patient_id: str,
    ) -> DoctorPatientDetailResponse:
        """Fetch the consolidated medical profile details for a specific treated patient"""
        
        # 1. Enforce validation: Patient must have at least one appointment or consultation with this doctor
        has_appt = await self.appointment_repository.exists({
            "patient_id": patient_id,
            "doctor_id": doctor_profile_id
        })
        has_cons = await self.consultation_repository.exists({
            "patient_id": patient_id,
            "doctor_id": doctor_profile_id
        })

        if not (has_appt or has_cons):
            raise ValueError("Patient not found or access denied")

        # 2. Fetch basic profile
        user = await self.user_repository.get(patient_id)
        if not user or user.role != UserRole.PATIENT:
            raise ValueError("Patient profile not found")

        # 3. Retrieve history and records
        # Appointments
        appt_docs = await self.appointment_repository.get_many(
            {"patient_id": patient_id, "doctor_id": doctor_profile_id},
            limit=1000
        )
        appt_docs.sort(key=lambda a: (a.slot_date, a.slot_time), reverse=True)
        appointments = [AppointmentResponse(**a.model_dump()) for a in appt_docs]

        # Consultations
        cons_docs = await self.consultation_repository.get_many(
            {"patient_id": patient_id, "doctor_id": doctor_profile_id},
            limit=1000
        )
        cons_docs.sort(key=lambda c: c.created_at, reverse=True)
        consultations = [ConsultationResponse(**c.model_dump()) for c in cons_docs]

        # Reports
        report_docs = await self.report_repository.get_many(
            {"patient_id": patient_id},
            limit=1000
        )
        report_docs.sort(key=lambda r: r.created_at, reverse=True)
        reports = [ReportResponse(**r.model_dump()) for r in report_docs]

        # Prescriptions
        pres_docs = await self.prescription_repository.get_many(
            {"patient_id": patient_id, "doctor_id": doctor_profile_id},
            limit=1000
        )
        pres_docs.sort(key=lambda p: p.created_at, reverse=True)
        prescriptions = [PrescriptionResponse(**p.model_dump()) for p in pres_docs]

        # Health insights
        insight_docs = await self.health_insight_repository.get_many(
            {"patient_id": patient_id},
            limit=1000
        )
        insight_docs.sort(key=lambda i: i.created_at, reverse=True)
        health_insights = [HealthInsightResponse(**i.model_dump()) for i in insight_docs]

        # Active reminders
        reminder_docs = await self.reminder_repository.get_many(
            {"patient_id": patient_id, "status": "active"},
            limit=1000
        )
        reminder_docs.sort(key=lambda r: r.created_at, reverse=True)
        current_reminders = [ReminderResponse(**r.model_dump()) for r in reminder_docs]

        # Latest doctor chat session
        doctor_profile = await self.doctor_profile_repository.get(doctor_profile_id)
        doctor_user_id = doctor_profile.user_id if doctor_profile else None

        chat_query: Dict[str, Any] = {
            "patient_id": patient_id,
            "session_type": "doctor_chat"
        }
        if doctor_user_id:
            chat_query["$or"] = [
                {"doctor_id": doctor_profile_id},
                {"doctor_user_id": doctor_user_id},
                {"doctor_id": doctor_user_id}
            ]
        else:
            chat_query["doctor_id"] = doctor_profile_id

        latest_chat_doc = await self.chat_session_repository.collection.find_one(
            chat_query,
            sort=[("last_message_at", -1)]
        )
        latest_chat_session = None
        if latest_chat_doc:
            from app.models.chat import ChatSessionInDB
            latest_chat_session = ChatSessionResponse(**ChatSessionInDB.from_mongo(latest_chat_doc).model_dump())

        # Fetch patient memory document
        db = self.user_repository.collection.database
        patient_mem_doc = await db.patient_memory.find_one({"patient_id": patient_id})
        patient_memory_data = None
        if patient_mem_doc:
            doc = dict(patient_mem_doc)
            if "_id" in doc:
                doc["id"] = str(doc.pop("_id"))
            if "patient_id" in doc:
                doc["patient_id"] = str(doc["patient_id"])
            if "last_updated" not in doc and "updated_at" in doc:
                doc["last_updated"] = doc.pop("updated_at")
            elif "last_updated" not in doc:
                doc["last_updated"] = datetime.now(timezone.utc)
            patient_memory_data = doc

        return DoctorPatientDetailResponse(
            profile=UserResponse(**user.model_dump()),
            appointment_history=appointments,
            consultation_history=consultations,
            reports=reports,
            prescriptions=prescriptions,
            health_insights=health_insights,
            current_reminders=current_reminders,
            latest_chat_session=latest_chat_session,
            patient_memory=patient_memory_data,
        )
