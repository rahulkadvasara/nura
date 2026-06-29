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
    get_reminder_service,
)
from app.schemas.reminder import (
    ReminderCreateSchema,
    ReminderUpdateSchema,
    ReminderResponse,
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


@router.get(
    "/reminders",
    response_model=SuccessResponse,
    summary="Get patient's active reminders",
)
async def get_patient_reminders(
    current_user: UserInDB = Depends(require_exact_patient),
    reminder_service = Depends(get_reminder_service),
):
    try:
        reminders = await reminder_service.list_active_reminders(str(current_user.id))
        data = [reminder_service.to_response(r).model_dump() for r in reminders]
        return SuccessResponse(success=True, message="Reminders retrieved", data=data)
    except Exception as e:
        logger.exception("Failed to retrieve reminders for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve reminders: {str(e)}"
        )


@router.post(
    "/reminders",
    response_model=SuccessResponse,
    summary="Create a new reminder",
)
async def create_patient_reminder(
    schema: ReminderCreateSchema,
    current_user: UserInDB = Depends(require_exact_patient),
    reminder_service = Depends(get_reminder_service),
):
    # Enforce patient_id check
    if schema.patient_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: patient_id mismatch."
        )
        
    try:
        # Enforce current user role context for safety overrides
        schema.user_role = current_user.role.value
        reminder = await reminder_service.create_reminder(schema)
        return SuccessResponse(
            success=True,
            message="Reminder created successfully",
            data=reminder_service.to_response(reminder).model_dump()
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.exception("Failed to create reminder for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create reminder: {str(e)}"
        )


@router.put(
    "/reminders/{reminder_id}",
    response_model=SuccessResponse,
    summary="Update an existing reminder",
)
async def update_patient_reminder(
    reminder_id: str,
    schema: ReminderUpdateSchema,
    current_user: UserInDB = Depends(require_exact_patient),
    reminder_service = Depends(get_reminder_service),
):
    existing = await reminder_service.get_reminder_by_id(reminder_id)
    if not existing or existing.patient_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found or access denied"
        )
        
    try:
        schema.user_role = current_user.role.value
        updated = await reminder_service.update_reminder(reminder_id, schema)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update reminder"
            )
        return SuccessResponse(
            success=True,
            message="Reminder updated successfully",
            data=reminder_service.to_response(updated).model_dump()
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as e:
        logger.exception("Failed to update reminder %s", reminder_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update reminder: {str(e)}"
        )


@router.delete(
    "/reminders/{reminder_id}",
    response_model=SuccessResponse,
    summary="Delete a reminder",
)
async def delete_patient_reminder(
    reminder_id: str,
    current_user: UserInDB = Depends(require_exact_patient),
    reminder_service = Depends(get_reminder_service),
):
    existing = await reminder_service.get_reminder_by_id(reminder_id)
    if not existing or existing.patient_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found or access denied"
        )
        
    try:
        success = await reminder_service.delete_reminder(reminder_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete reminder"
            )
        return SuccessResponse(
            success=True,
            message="Reminder deleted successfully"
        )
    except Exception as e:
        logger.exception("Failed to delete reminder %s", reminder_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete reminder: {str(e)}"
        )
