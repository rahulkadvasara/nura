"""
Nura - Database Initialization
Setup MongoDB collections with indexes
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


async def setup_database(database: AsyncIOMotorDatabase) -> None:
    """Initialize database collections and indexes"""
    
    logger.info("Setting up database collections and indexes...")
    
    # Users collection
    users_collection = database.users
    await users_collection.create_index("email", unique=True, name="email_unique")
    await users_collection.create_index("role", name="role_index")
    await users_collection.create_index("is_active", name="is_active_index")
    await users_collection.create_index("created_at", name="created_at_index")
    logger.info("Created users collection indexes")
    
    # Refresh tokens collection
    refresh_tokens_collection = database.refresh_tokens
    await refresh_tokens_collection.create_index("user_id", name="user_id_index")
    await refresh_tokens_collection.create_index("token_hash", unique=True, name="token_hash_unique")
    await refresh_tokens_collection.create_index("expires_at", name="expires_at_index")
    await refresh_tokens_collection.create_index("revoked", name="revoked_index")
    await refresh_tokens_collection.create_index([("user_id", 1), ("revoked", 1), ("expires_at", 1)], name="active_tokens_index")
    logger.info("Created refresh_tokens collection indexes")
    
    # OTP verifications collection
    otp_verifications_collection = database.otp_verifications
    await otp_verifications_collection.create_index("email", name="email_index")
    await otp_verifications_collection.create_index("purpose", name="purpose_index")
    await otp_verifications_collection.create_index("expires_at", name="expires_at_index")
    await otp_verifications_collection.create_index("verified", name="verified_index")
    await otp_verifications_collection.create_index([("email", 1), ("purpose", 1), ("verified", 1), ("expires_at", 1)], name="valid_otps_index")
    await otp_verifications_collection.create_index([("email", 1), ("purpose", 1), ("created_at", -1)], name="latest_otp_index")
    logger.info("Created otp_verifications collection indexes")

    # -----------------------------------------------------------------------
    # Doctor Foundation indexes
    # -----------------------------------------------------------------------

    # doctor_profiles collection
    doctor_profiles_collection = database.doctor_profiles
    # Fast lookup of a profile by owning user (unique — one profile per user)
    await doctor_profiles_collection.create_index("user_id", unique=True, name="user_id_unique")
    # Admin / search filtering by verification status
    await doctor_profiles_collection.create_index("profile_status", name="profile_status_index")
    # Doctor discovery / sorting support
    await doctor_profiles_collection.create_index("specialization", name="specialization_index")
    await doctor_profiles_collection.create_index("consultation_fee", name="consultation_fee_index")
    await doctor_profiles_collection.create_index("average_rating", name="average_rating_index")
    await doctor_profiles_collection.create_index("experience_years", name="experience_years_index")
    # Compound index for verified doctor search
    await doctor_profiles_collection.create_index(
        [("profile_status", 1), ("specialization", 1), ("consultation_fee", 1)],
        name="doctor_search_compound_index",
    )
    logger.info("Created doctor_profiles collection indexes")

    # doctor_documents collection
    doctor_documents_collection = database.doctor_documents
    # Fetch all documents for a given doctor quickly
    await doctor_documents_collection.create_index("doctor_id", name="doctor_id_index")
    # Admin queue: all pending documents
    await doctor_documents_collection.create_index("verification_status", name="verification_status_index")
    # Compound index for filtering a doctor's documents by status
    await doctor_documents_collection.create_index(
        [("doctor_id", 1), ("verification_status", 1)],
        name="doctor_doc_status_compound_index",
    )
    await doctor_documents_collection.create_index("uploaded_at", name="uploaded_at_index")
    logger.info("Created doctor_documents collection indexes")

    # doctor_availability collection
    doctor_availability_collection = database.doctor_availability
    # Fetch all slots for a given doctor quickly
    await doctor_availability_collection.create_index("doctor_id", name="doctor_id_index")
    # Day-level lookups
    await doctor_availability_collection.create_index("day_of_week", name="day_of_week_index")
    # Active slot filtering
    await doctor_availability_collection.create_index("active", name="active_index")
    # Compound index for common query pattern: doctor + day + active
    await doctor_availability_collection.create_index(
        [("doctor_id", 1), ("day_of_week", 1), ("active", 1)],
        name="doctor_availability_compound_index",
    )
    logger.info("Created doctor_availability collection indexes")
    
    logger.info("Database setup completed")