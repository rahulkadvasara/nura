"""
Nura - Doctor Application Router
Authenticated patient-only endpoints for applying to become a doctor
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId

from app.models.user import UserInDB, UserRole
from app.models.doctor import (
    DoctorProfileStatus,
    DocumentType,
    DocumentVerificationStatus,
    DoctorDocumentUpdate,
    DoctorProfileInDB,
)
from app.schemas.auth import SuccessResponse
from app.schemas.doctor import (
    DoctorApplicationRequest,
    DoctorApplicationUpdateSchema,
    DoctorApplicationResponse,
    DoctorProfileCreateSchema,
    DoctorProfileUpdateSchema,
    DoctorDocumentCreateSchema,
    DoctorAvailabilityCreateSchema,
    DoctorAvailabilityUpdateSchema,
    DoctorAvailabilityResponse,
    DoctorProfileManagementUpdateSchema,
    DoctorProfileManagementResponse,
)
from app.schemas.appointment import (
    DoctorAppointmentItem,
    AppointmentRejectSchema,
    AppointmentResponse,
    ConsultationCompleteSchema,
    ConsultationResponse,
    DoctorConsultationItemResponse,
    PrescriptionCreateRequestSchema,
    PrescriptionUpdateSchema,
    PrescriptionResponse,
)
from app.core.dependencies import (
    require_active_user,
    get_doctor_profile_service,
    get_doctor_document_service,
    get_doctor_availability_service,
    require_verified_doctor,
    get_appointment_service,
    get_notification_service,
    get_audit_log_service,
    get_consultation_service,
    get_prescription_service,
    get_doctor_patient_service,
)
from app.services.doctor_service import DoctorProfileService, DoctorDocumentService, DoctorAvailabilityService
from app.services.appointment_service import AppointmentService
from app.services.notification_service import NotificationService
from app.services.audit_log_service import AuditLogService
from app.services.consultation_service import ConsultationService
from app.services.prescription_service import PrescriptionService
from app.services.doctor_patient_service import DoctorPatientService
from app.schemas.doctor_patient import DoctorPatientListResponse, DoctorPatientDetailResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_application_status(profile_status: DoctorProfileStatus) -> str:
    """Map DoctorProfileStatus to application UI status string"""
    if profile_status == DoctorProfileStatus.PENDING:
        return "Pending Review"
    elif profile_status == DoctorProfileStatus.VERIFIED:
        return "Approved"
    elif profile_status == DoctorProfileStatus.REJECTED:
        return "Rejected"
    return "Unknown"


@router.post(
    "/apply",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for Doctor Status",
    description="Submit specialization, educational details, and verification documents to apply as a doctor."
)
async def apply_doctor(
    schema: DoctorApplicationRequest,
    current_user: UserInDB = Depends(require_active_user),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """
    Submit a doctor application.
    Requires strictly PATIENT role.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can apply for doctor status"
        )

    # Check if application already exists
    existing_profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
    if existing_profile:
        if existing_profile.profile_status == DoctorProfileStatus.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already verified as a doctor"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor application already exists"
        )

    try:
        # 1. Create doctor profile with status pending
        profile_create = DoctorProfileCreateSchema(
            specialization=schema.specialization,
            qualifications=[],  # Not used explicitly, we use education instead
            experience_years=schema.experience_years,
            consultation_fee=schema.consultation_fee,
            bio=schema.bio,
            languages=schema.languages,
            hospital=schema.hospital,
            license_number=schema.license_number,
            education=schema.education
        )
        profile = await doctor_profile_service.create_profile(current_user.id, profile_create)

        # 2. Upload verification documents (metadata only)
        documents_to_upload = [
            (DocumentType.DEGREE, schema.degree_certificate_url),
            (DocumentType.LICENSE, schema.medical_license_url),
            (DocumentType.ID_PROOF, schema.identity_proof_url)
        ]

        for doc_type, url in documents_to_upload:
            doc_create = DoctorDocumentCreateSchema(
                document_type=doc_type,
                document_url=url
            )
            await doctor_document_service.upload_document(profile.id, doc_create)

        # Retrieve newly created documents
        docs = await doctor_document_service.get_documents_by_doctor(profile.id)

        response_data = DoctorApplicationResponse(
            application_status=get_application_status(profile.profile_status),
            profile_status=profile.profile_status,
            profile=doctor_profile_service.to_response(profile),
            documents=[doctor_document_service.to_response(d) for d in docs]
        )

        return SuccessResponse(
            success=True,
            message="Doctor application submitted successfully",
            data=response_data.model_dump()
        )

    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to submit doctor application for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit doctor application"
        ) from exc


@router.get(
    "/application",
    response_model=SuccessResponse,
    summary="Get Doctor Application Status",
    description="Retrieve the current status, profile, and documents submitted for verification."
)
async def get_application(
    current_user: UserInDB = Depends(require_active_user),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """
    Retrieve user's doctor application.
    Requires strictly PATIENT role.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can check doctor application status"
        )

    profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor application found"
        )

    docs = await doctor_document_service.get_documents_by_doctor(profile.id)

    response_data = DoctorApplicationResponse(
        application_status=get_application_status(profile.profile_status),
        profile_status=profile.profile_status,
        profile=doctor_profile_service.to_response(profile),
        documents=[doctor_document_service.to_response(d) for d in docs]
    )

    return SuccessResponse(
        success=True,
        message="Doctor application retrieved successfully",
        data=response_data.model_dump()
    )


@router.put(
    "/application",
    response_model=SuccessResponse,
    summary="Update Pending Doctor Application",
    description="Allows updating fields and documents of a doctor application while it is still pending."
)
async def update_application(
    schema: DoctorApplicationUpdateSchema,
    current_user: UserInDB = Depends(require_active_user),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """
    Update pending doctor application.
    Requires strictly PATIENT role.
    """
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can update doctor application details"
        )

    profile = await doctor_profile_service.get_profile_by_user_id(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No doctor application found"
        )

    if profile.profile_status != DoctorProfileStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending applications can be updated"
        )

    try:
        # 1. Update profile details
        profile_update = DoctorProfileUpdateSchema(
            specialization=schema.specialization,
            qualifications=None,
            experience_years=schema.experience_years,
            consultation_fee=schema.consultation_fee,
            bio=schema.bio,
            languages=schema.languages,
            hospital=schema.hospital,
            license_number=schema.license_number,
            education=schema.education
        )
        updated_profile = await doctor_profile_service.update_profile(profile.id, profile_update)
        if not updated_profile:
            raise RuntimeError("Failed to update doctor profile")

        # 2. Update documents (metadata urls only)
        docs = await doctor_document_service.get_documents_by_doctor(profile.id)

        document_updates = [
            (DocumentType.DEGREE, schema.degree_certificate_url),
            (DocumentType.LICENSE, schema.medical_license_url),
            (DocumentType.ID_PROOF, schema.identity_proof_url)
        ]

        for doc_type, url in document_updates:
            if url is not None:
                existing_docs = [d for d in docs if d.document_type == doc_type]
                if existing_docs:
                    # Update existing document url and reset status to pending
                    doc_update = DoctorDocumentUpdate(
                        document_url=url,
                        verification_status=DocumentVerificationStatus.PENDING
                    )
                    await doctor_document_service.document_repository.update(existing_docs[0].id, doc_update)
                else:
                    # Upload/Create new document url
                    doc_create = DoctorDocumentCreateSchema(
                        document_type=doc_type,
                        document_url=url
                    )
                    await doctor_document_service.upload_document(profile.id, doc_create)

        # Retrieve updated documents list
        updated_docs = await doctor_document_service.get_documents_by_doctor(profile.id)

        response_data = DoctorApplicationResponse(
            application_status=get_application_status(updated_profile.profile_status),
            profile_status=updated_profile.profile_status,
            profile=doctor_profile_service.to_response(updated_profile),
            documents=[doctor_document_service.to_response(d) for d in updated_docs]
        )

        return SuccessResponse(
            success=True,
            message="Doctor application updated successfully",
            data=response_data.model_dump()
        )

    except Exception as exc:
        logger.exception("Failed to update doctor application for user %s", current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update doctor application"
        ) from exc


# ---------------------------------------------------------------------------
# Doctor Availability Management
# ---------------------------------------------------------------------------

@router.get(
    "/availability",
    response_model=SuccessResponse,
    summary="Get Doctor Availability Slots",
    description="Retrieve all availability slots for the verified doctor."
)
async def get_availability(
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
) -> SuccessResponse:
    """Get all slots for the authenticated verified doctor."""
    try:
        slots = await doctor_availability_service.get_availability_by_doctor(current_doctor.id)
        return SuccessResponse(
            success=True,
            message="Doctor availability slots retrieved successfully",
            data={"availability": [doctor_availability_service.to_response(s).model_dump() for s in slots]}
        )
    except Exception as exc:
        logger.exception("Failed to retrieve availability slots for doctor %s", current_doctor.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve availability slots"
        ) from exc


@router.post(
    "/availability",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Doctor Availability Slot",
    description="Create a new availability slot for the verified doctor."
)
async def create_availability_slot(
    schema: DoctorAvailabilityCreateSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
) -> SuccessResponse:
    """Create a new availability slot. Validates overlaps and duration."""
    try:
        created_slot = await doctor_availability_service.create_availability(current_doctor.id, schema)
        return SuccessResponse(
            success=True,
            message="Doctor availability slot created successfully",
            data=doctor_availability_service.to_response(created_slot).model_dump()
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to create availability slot for doctor %s", current_doctor.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create availability slot"
        ) from exc


@router.put(
    "/availability/{slot_id}",
    response_model=SuccessResponse,
    summary="Update Doctor Availability Slot",
    description="Update an existing availability slot if not booked by an approved appointment."
)
async def update_availability_slot(
    slot_id: str,
    schema: DoctorAvailabilityUpdateSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
) -> SuccessResponse:
    """Update an existing availability slot. Prevents updates if the slot has an approved appointment."""
    existing_slot = await doctor_availability_service.get_availability_by_id(slot_id)
    if not existing_slot or existing_slot.doctor_id != current_doctor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )

    try:
        updated = await doctor_availability_service.update_availability(slot_id, schema)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update availability slot"
            )
        return SuccessResponse(
            success=True,
            message="Doctor availability slot updated successfully",
            data=doctor_availability_service.to_response(updated).model_dump()
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to update availability slot %s for doctor %s", slot_id, current_doctor.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update availability slot"
        ) from exc


@router.delete(
    "/availability/{slot_id}",
    response_model=SuccessResponse,
    summary="Delete Doctor Availability Slot",
    description="Delete an existing availability slot if not booked by an approved appointment."
)
async def delete_availability_slot(
    slot_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_availability_service: DoctorAvailabilityService = Depends(get_doctor_availability_service),
) -> SuccessResponse:
    """Delete an availability slot. Prevents deletion if the slot has an approved appointment."""
    existing_slot = await doctor_availability_service.get_availability_by_id(slot_id)
    if not existing_slot or existing_slot.doctor_id != current_doctor.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Availability slot not found"
        )

    try:
        success = await doctor_availability_service.delete_availability(slot_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete availability slot"
            )
        return SuccessResponse(
            success=True,
            message="Doctor availability slot deleted successfully"
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to delete availability slot %s for doctor %s", slot_id, current_doctor.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete availability slot"
        ) from exc


# ---------------------------------------------------------------------------
# Doctor Profile Management
# ---------------------------------------------------------------------------

@router.get(
    "/profile",
    response_model=SuccessResponse,
    summary="Get Doctor Self Profile",
    description="Retrieve detailed profile and documents verification status for the verified doctor."
)
async def get_doctor_profile(
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """Retrieve detailed practitioner profile and credentials statuses."""
    try:
        docs = await doctor_document_service.get_documents_by_doctor(current_doctor.id)
        response_data = DoctorProfileManagementResponse(
            profile=doctor_profile_service.to_response(current_doctor),
            documents=[doctor_document_service.to_response(d) for d in docs]
        )
        return SuccessResponse(
            success=True,
            message="Doctor profile retrieved successfully",
            data=response_data.model_dump()
        )
    except Exception as exc:
        logger.exception("Failed to retrieve doctor profile for user %s", current_doctor.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve doctor profile"
        ) from exc


@router.put(
    "/profile",
    response_model=SuccessResponse,
    summary="Update Doctor Self Profile",
    description="Update self-managed profile settings (bio, fee, languages, education, experience)."
)
async def update_doctor_profile(
    schema: DoctorProfileManagementUpdateSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_profile_service: DoctorProfileService = Depends(get_doctor_profile_service),
    doctor_document_service: DoctorDocumentService = Depends(get_doctor_document_service),
) -> SuccessResponse:
    """Update practitioner profile details (bio, fee, languages, education, experience)."""
    try:
        updated = await doctor_profile_service.update_doctor_profile_management(current_doctor.id, schema)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update doctor profile"
            )
        docs = await doctor_document_service.get_documents_by_doctor(current_doctor.id)
        response_data = DoctorProfileManagementResponse(
            profile=doctor_profile_service.to_response(updated),
            documents=[doctor_document_service.to_response(d) for d in docs]
        )
        return SuccessResponse(
            success=True,
            message="Doctor profile updated successfully",
            data=response_data.model_dump()
        )
    except Exception as exc:
        logger.exception("Failed to update doctor profile for user %s", current_doctor.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update doctor profile"
        ) from exc


@router.get(
    "/appointments",
    response_model=SuccessResponse,
    summary="Get Doctor Appointment Queue",
    description="Retrieves the appointment request queue (pending, approved, rejected) for the logged-in verified doctor.",
)
async def get_doctor_appointments(
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        queue = await appointment_service.list_doctor_appointments(current_doctor.id)
        return SuccessResponse(
            success=True,
            message="Doctor appointments queue retrieved successfully",
            data={"appointments": queue},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve doctor appointments queue")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointments queue",
        ) from exc


@router.get(
    "/appointments/{appointment_id}",
    response_model=SuccessResponse,
    summary="Get Doctor Appointment Details",
    description="Retrieves detailed information of a specific appointment belonging to this doctor.",
)
async def get_doctor_appointment_details(
    appointment_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> SuccessResponse:
    try:
        appointment = await appointment_service.get_appointment_by_id(appointment_id)
        if not appointment or appointment.doctor_id != current_doctor.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment request not found",
            )
        return SuccessResponse(
            success=True,
            message="Appointment details retrieved successfully",
            data=appointment_service.to_response(appointment).model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve doctor appointment details for %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointment details",
        ) from exc


@router.post(
    "/appointments/{appointment_id}/approve",
    response_model=SuccessResponse,
    summary="Approve Appointment Request",
    description="Allows a verified doctor to approve a pending appointment request.",
)
async def approve_appointment(
    appointment_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
    notification_service: NotificationService = Depends(get_notification_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        approved = await appointment_service.approve_appointment(
            appointment_id=appointment_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_doctor.user_id,
            notification_service=notification_service,
            audit_log_service=audit_log_service,
        )
        return SuccessResponse(
            success=True,
            message="Appointment request approved successfully",
            data=appointment_service.to_response(approved).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to approve appointment request %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve appointment request",
        ) from exc


@router.post(
    "/appointments/{appointment_id}/reject",
    response_model=SuccessResponse,
    summary="Reject Appointment Request",
    description="Allows a verified doctor to reject a pending appointment request with a reason.",
)
async def reject_appointment(
    appointment_id: str,
    schema: AppointmentRejectSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
    notification_service: NotificationService = Depends(get_notification_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        rejected = await appointment_service.reject_appointment(
            appointment_id=appointment_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_doctor.user_id,
            rejection_reason=schema.rejection_reason,
            notification_service=notification_service,
            audit_log_service=audit_log_service,
        )
        return SuccessResponse(
            success=True,
            message="Appointment request rejected successfully",
            data=appointment_service.to_response(rejected).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to reject appointment request %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject appointment request",
        ) from exc


@router.post(
    "/appointments/{appointment_id}/start",
    response_model=SuccessResponse,
    summary="Start Consultation",
    description="Transition appointment state from approved to in_progress and record start time.",
)
async def start_consultation(
    appointment_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        updated = await appointment_service.start_consultation(
            appointment_id=appointment_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_doctor.user_id,
            audit_log_service=audit_log_service,
        )
        return SuccessResponse(
            success=True,
            message="Consultation started successfully",
            data=appointment_service.to_response(updated).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to start consultation for %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start consultation",
        ) from exc


@router.post(
    "/appointments/{appointment_id}/complete",
    response_model=SuccessResponse,
    summary="Complete Consultation",
    description="Complete the active consultation, create the consultation record, and update appointment to completed.",
)
async def complete_consultation(
    appointment_id: str,
    schema: ConsultationCompleteSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    appointment_service: AppointmentService = Depends(get_appointment_service),
    consultation_service: ConsultationService = Depends(get_consultation_service),
    notification_service: NotificationService = Depends(get_notification_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        consultation = await appointment_service.complete_consultation(
            appointment_id=appointment_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_doctor.user_id,
            schema=schema,
            consultation_service=consultation_service,
            notification_service=notification_service,
            audit_log_service=audit_log_service,
        )
        return SuccessResponse(
            success=True,
            message="Consultation completed successfully",
            data=consultation_service.to_response(consultation).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to complete consultation for %s", appointment_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete consultation",
        ) from exc


@router.get(
    "/consultations",
    response_model=SuccessResponse,
    summary="Get Doctor's Consultations List",
    description="Retrieves a list of consultation records created by the logged-in doctor.",
)
async def get_doctor_consultations(
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    consultation_service: ConsultationService = Depends(get_consultation_service),
) -> SuccessResponse:
    try:
        from app.core.dependencies import get_user_repository
        user_repository = get_user_repository()
        queue = await consultation_service.list_doctor_consultations(
            doctor_profile_id=current_doctor.id,
            user_repository=user_repository,
        )
        return SuccessResponse(
            success=True,
            message="Consultations retrieved successfully",
            data={"consultations": queue},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve doctor consultations list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consultations list",
        ) from exc


@router.get(
    "/consultations/{consultation_id}",
    response_model=SuccessResponse,
    summary="Get Consultation Details",
    description="Retrieves detailed information of a specific consultation record.",
)
async def get_consultation_details(
    consultation_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    consultation_service: ConsultationService = Depends(get_consultation_service),
) -> SuccessResponse:
    try:
        consultation = await consultation_service.get_consultation_by_id(consultation_id)
        if not consultation or consultation.doctor_id != current_doctor.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )
        return SuccessResponse(
            success=True,
            message="Consultation details retrieved successfully",
            data=consultation_service.to_response(consultation).model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve consultation details for %s", consultation_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve consultation details",
        ) from exc


@router.post(
    "/consultations/{consultation_id}/prescription",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Prescription",
    description="Create a new prescription for a completed consultation."
)
async def create_prescription(
    consultation_id: str,
    schema: PrescriptionCreateRequestSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    current_user: UserInDB = Depends(require_active_user),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
    notification_service: NotificationService = Depends(get_notification_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        from app.core.dependencies import get_user_repository
        user_repo = get_user_repository()
        created = await prescription_service.create_prescription(
            consultation_id=consultation_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_user.id,
            schema=schema,
            notification_service=notification_service,
            audit_log_service=audit_log_service,
            user_repository=user_repo,
        )
        return SuccessResponse(
            success=True,
            message="Prescription created successfully",
            data=prescription_service.to_response(created).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to create prescription")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prescription",
        ) from exc


@router.put(
    "/prescriptions/{prescription_id}",
    response_model=SuccessResponse,
    summary="Update Prescription",
    description="Updates medications, instructions, or notes for a prescription if the consultation is completed."
)
async def update_prescription(
    prescription_id: str,
    schema: PrescriptionUpdateSchema,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    current_user: UserInDB = Depends(require_active_user),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
    appointment_service: AppointmentService = Depends(get_appointment_service),
    audit_log_service: AuditLogService = Depends(get_audit_log_service),
) -> SuccessResponse:
    try:
        updated = await prescription_service.update_prescription(
            prescription_id=prescription_id,
            doctor_profile_id=current_doctor.id,
            doctor_user_id=current_user.id,
            schema=schema,
            appointment_repository=appointment_service.appointment_repository,
            audit_log_service=audit_log_service,
        )
        return SuccessResponse(
            success=True,
            message="Prescription updated successfully",
            data=prescription_service.to_response(updated).model_dump(),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Failed to update prescription")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prescription",
        ) from exc


@router.get(
    "/prescriptions",
    response_model=SuccessResponse,
    summary="Get Doctor's Prescriptions List",
    description="Retrieves a list of prescriptions issued by the logged-in doctor."
)
async def get_doctor_prescriptions(
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> SuccessResponse:
    try:
        prescriptions = await prescription_service.list_prescriptions_by_doctor(current_doctor.id)
        data = [prescription_service.to_response(p).model_dump() for p in prescriptions]
        return SuccessResponse(
            success=True,
            message="Prescriptions retrieved successfully",
            data={"prescriptions": data},
        )
    except Exception as exc:
        logger.exception("Failed to retrieve prescriptions list")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prescriptions list",
        ) from exc


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=SuccessResponse,
    summary="Get Prescription Details",
    description="Retrieves detailed information of a specific prescription record."
)
async def get_doctor_prescription_details(
    prescription_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> SuccessResponse:
    try:
        prescription = await prescription_service.get_prescription_by_id(prescription_id)
        if not prescription or prescription.doctor_id != current_doctor.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prescription not found",
            )
        return SuccessResponse(
            success=True,
            message="Prescription details retrieved successfully",
            data=prescription_service.to_response(prescription).model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to retrieve prescription details")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prescription details",
        ) from exc


@router.get(
    "/patients",
    response_model=SuccessResponse,
    summary="List Doctor Patients",
    description="List all patients treated by the logged-in verified doctor. Supports search, sorting, and pagination."
)
async def list_patients(
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_patient_service: DoctorPatientService = Depends(get_doctor_patient_service),
) -> SuccessResponse:
    try:
        patients, total = await doctor_patient_service.get_patients(
            doctor_profile_id=current_doctor.id,
            search=search,
            sort_by=sort_by,
            limit=limit,
            skip=skip,
        )
        response_data = DoctorPatientListResponse(patients=patients, total=total)
        return SuccessResponse(
            success=True,
            message="Doctor's patients directory retrieved successfully",
            data=response_data.model_dump(),
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patients list for doctor %s", current_doctor.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients list",
        ) from exc


@router.get(
    "/patients/{patient_id}",
    response_model=SuccessResponse,
    summary="Get Patient Consolidated Details",
    description="Retrieve aggregated medical profiles, appointment history, report analytics, and active reminders."
)
async def get_patient_details(
    patient_id: str,
    current_doctor: DoctorProfileInDB = Depends(require_verified_doctor),
    doctor_patient_service: DoctorPatientService = Depends(get_doctor_patient_service),
) -> SuccessResponse:
    try:
        details = await doctor_patient_service.get_patient_detail(
            doctor_profile_id=current_doctor.id,
            patient_id=patient_id,
        )
        return SuccessResponse(
            success=True,
            message="Patient medical profile details retrieved successfully",
            data=details.model_dump(),
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(val_err)
        )
    except Exception as exc:
        logger.exception("Failed to retrieve patient medical profile details for patient %s", patient_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient medical profile details",
        ) from exc


