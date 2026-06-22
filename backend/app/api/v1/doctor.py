"""
Nura - Doctor Application Router
Authenticated patient-only endpoints for applying to become a doctor
"""

import logging
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
from app.core.dependencies import (
    require_active_user,
    get_doctor_profile_service,
    get_doctor_document_service,
    get_doctor_availability_service,
    require_verified_doctor,
)
from app.services.doctor_service import DoctorProfileService, DoctorDocumentService, DoctorAvailabilityService

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
