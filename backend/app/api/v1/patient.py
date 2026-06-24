"""
Nura - Patient Router
Authenticated patient-only endpoints for viewing consultation history and prescriptions
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.user import UserInDB, UserRole
from app.schemas.auth import SuccessResponse
from app.schemas.appointment import (
    PatientConsultationItemResponse,
    PatientPrescriptionResponse,
    MedicationSchema,
)
from app.core.dependencies import (
    require_active_user,
    require_exact_patient,
    get_consultation_service,
    get_prescription_service,
    get_doctor_profile_repository,
    get_user_repository,
    get_appointment_repository,
)
from app.services.consultation_service import ConsultationService
from app.services.prescription_service import PrescriptionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/consultations",
    response_model=SuccessResponse,
    summary="Get Patient's Consultation History",
    description="Retrieves a list of consultation records for the logged-in patient.",
)
async def get_patient_consultations(
    current_user: UserInDB = Depends(require_exact_patient),
    consultation_service: ConsultationService = Depends(get_consultation_service),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> SuccessResponse:
    try:
        doctor_profile_repo = get_doctor_profile_repository()
        user_repo = get_user_repository()
        appointment_repo = get_appointment_repository()
        prescription_repo = prescription_service.prescription_repository
        
        history = await consultation_service.list_patient_consultation_history(
            patient_id=current_user.id,
            doctor_profile_repository=doctor_profile_repo,
            user_repository=user_repo,
            appointment_repository=appointment_repo,
            prescription_repository=prescription_repo,
        )
        return SuccessResponse(
            success=True,
            message="Consultation history retrieved successfully",
            data={"consultations": history},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patient consultation history")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consultation history",
        ) from exc


@router.get(
    "/consultations/{consultation_id}",
    response_model=SuccessResponse,
    summary="Get Patient Consultation Details",
    description="Retrieves detailed information of a specific consultation record for the patient.",
)
async def get_patient_consultation_details(
    consultation_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    consultation_service: ConsultationService = Depends(get_consultation_service),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> SuccessResponse:
    try:
        consultation = await consultation_service.get_consultation_by_id(consultation_id)
        if not consultation or consultation.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )
            
        doctor_profile_repo = get_doctor_profile_repository()
        user_repo = get_user_repository()
        appointment_repo = get_appointment_repository()
        prescription_repo = prescription_service.prescription_repository
        
        # We can map it to PatientConsultationItemResponse schema for rich info
        doctor_profile = await doctor_profile_repo.get(consultation.doctor_id)
        doctor_name = "Unknown Doctor"
        specialization = "General Medicine"
        if doctor_profile:
            specialization = doctor_profile.specialization
            doctor_user = await user_repo.get(doctor_profile.user_id)
            if doctor_user:
                doctor_name = doctor_user.full_name
                
        appointment = await appointment_repo.get(consultation.appointment_id)
        appointment_date = "Unknown Date"
        appointment_time = "Unknown Time"
        if appointment:
            appointment_date = appointment.slot_date
            appointment_time = appointment.slot_time

        prescription = await prescription_repo.get_by_consultation_id(consultation.id)
        prescription_status = "No Prescription"
        prescription_id = None
        if prescription:
            prescription_status = "Prescribed"
            prescription_id = prescription.id

        details = PatientConsultationItemResponse(
            id=consultation.id,
            appointment_id=consultation.appointment_id,
            patient_id=consultation.patient_id,
            doctor_id=consultation.doctor_id,
            doctor_name=doctor_name,
            doctor_specialization=specialization,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            diagnosis=consultation.diagnosis,
            consultation_notes=consultation.consultation_notes,
            follow_up_required=consultation.follow_up_required,
            follow_up_date=consultation.follow_up_date,
            prescription_status=prescription_status,
            prescription_id=prescription_id,
            created_at=consultation.created_at,
            updated_at=consultation.updated_at,
        )
        return SuccessResponse(
            success=True,
            message="Consultation details retrieved successfully",
            data=details.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve consultation details for %s", consultation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consultation details",
        ) from exc


@router.get(
    "/prescriptions",
    response_model=SuccessResponse,
    summary="Get Patient's Prescriptions List",
    description="Retrieves a list of prescriptions issued for the logged-in patient.",
)
async def get_patient_prescriptions(
    current_user: UserInDB = Depends(require_exact_patient),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
    consultation_service: ConsultationService = Depends(get_consultation_service),
) -> SuccessResponse:
    try:
        prescriptions = await prescription_service.list_prescriptions_by_patient(current_user.id)
        # Sort prescriptions by created_at descending (newest first)
        prescriptions.sort(key=lambda p: p.created_at, reverse=True)
        
        doctor_profile_repo = get_doctor_profile_repository()
        user_repo = get_user_repository()
        
        resolved = []
        for p in prescriptions:
            # Resolve diagnosis and doctor details
            consultation = await consultation_service.get_consultation_by_id(p.consultation_id)
            diagnosis = "No diagnosis on record"
            if consultation:
                diagnosis = consultation.diagnosis
                
            doctor_profile = await doctor_profile_repo.get(p.doctor_id)
            doctor_name = "Unknown Doctor"
            specialization = "General Medicine"
            if doctor_profile:
                specialization = doctor_profile.specialization
                doctor_user = await user_repo.get(doctor_profile.user_id)
                if doctor_user:
                    doctor_name = doctor_user.full_name
            
            meds = [
                {
                    "drug_name": m.drug_name,
                    "dosage": m.dosage,
                    "frequency": m.frequency,
                    "duration": m.duration,
                    "instructions": getattr(m, "instructions", None),
                }
                for m in p.medications
            ]
            
            resolved.append({
                "id": p.id,
                "consultation_id": p.consultation_id,
                "patient_id": p.patient_id,
                "doctor_id": p.doctor_id,
                "doctor_name": doctor_name,
                "doctor_specialization": specialization,
                "diagnosis": diagnosis,
                "medications": meds,
                "dosage_instructions": p.dosage_instructions,
                "notes": p.notes,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            })
            
        return SuccessResponse(
            success=True,
            message="Prescriptions retrieved successfully",
            data={"prescriptions": resolved},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patient prescriptions")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prescriptions list",
        ) from exc


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=SuccessResponse,
    summary="Get Patient Prescription Details",
    description="Retrieves detailed information of a specific prescription record for the patient.",
)
async def get_patient_prescription_details(
    prescription_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
    consultation_service: ConsultationService = Depends(get_consultation_service),
) -> SuccessResponse:
    try:
        prescription = await prescription_service.get_prescription_by_id(prescription_id)
        if not prescription or prescription.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
            
        doctor_profile_repo = get_doctor_profile_repository()
        user_repo = get_user_repository()
        
        # Resolve diagnosis and doctor details
        consultation = await consultation_service.get_consultation_by_id(prescription.consultation_id)
        diagnosis = "No diagnosis on record"
        if consultation:
            diagnosis = consultation.diagnosis
            
        doctor_profile = await doctor_profile_repo.get(prescription.doctor_id)
        doctor_name = "Unknown Doctor"
        specialization = "General Medicine"
        if doctor_profile:
            specialization = doctor_profile.specialization
            doctor_user = await user_repo.get(doctor_profile.user_id)
            if doctor_user:
                doctor_name = doctor_user.full_name
                
        meds = [
            MedicationSchema(
                drug_name=m.drug_name,
                dosage=m.dosage,
                frequency=m.frequency,
                duration=m.duration,
                instructions=getattr(m, "instructions", None),
            )
            for m in prescription.medications
        ]
        
        details = PatientPrescriptionResponse(
            id=prescription.id,
            consultation_id=prescription.consultation_id,
            patient_id=prescription.patient_id,
            doctor_id=prescription.doctor_id,
            doctor_name=doctor_name,
            doctor_specialization=specialization,
            diagnosis=diagnosis,
            medications=meds,
            dosage_instructions=prescription.dosage_instructions,
            notes=prescription.notes,
            created_at=prescription.created_at,
            updated_at=prescription.updated_at,
        )
        return SuccessResponse(
            success=True,
            message="Prescription details retrieved successfully",
            data=details.model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve prescription details for %s", prescription_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prescription details",
        ) from exc
