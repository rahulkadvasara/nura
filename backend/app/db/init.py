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

    # appointments collection
    appointments_collection = database.appointments
    await appointments_collection.create_index("patient_id", name="patient_id_index")
    await appointments_collection.create_index("doctor_id", name="doctor_id_index")
    await appointments_collection.create_index("status", name="status_index")
    await appointments_collection.create_index("slot_date", name="slot_date_index")
    logger.info("Created appointments collection indexes")

    # consultations collection
    consultations_collection = database.consultations
    await consultations_collection.create_index("appointment_id", name="appointment_id_index")
    await consultations_collection.create_index("patient_id", name="patient_id_index")
    await consultations_collection.create_index("doctor_id", name="doctor_id_index")
    logger.info("Created consultations collection indexes")

    # prescriptions collection
    prescriptions_collection = database.prescriptions
    await prescriptions_collection.create_index("consultation_id", name="consultation_id_index")
    await prescriptions_collection.create_index("patient_id", name="patient_id_index")
    await prescriptions_collection.create_index("doctor_id", name="doctor_id_index")
    logger.info("Created prescriptions collection indexes")

    # reports collection
    reports_collection = database.reports
    await reports_collection.create_index("patient_id", name="patient_id_index")
    await reports_collection.create_index("report_type", name="report_type_index")
    await reports_collection.create_index("processing_status", name="processing_status_index")
    await reports_collection.create_index("created_at", name="created_at_index")
    logger.info("Created reports collection indexes")

    # health_insights collection
    health_insights_collection = database.health_insights
    await health_insights_collection.create_index("patient_id", name="patient_id_index")
    await health_insights_collection.create_index("severity", name="severity_index")
    await health_insights_collection.create_index("insight_type", name="insight_type_index")
    logger.info("Created health_insights collection indexes")

    # reminders collection
    reminders_collection = database.reminders
    await reminders_collection.create_index("patient_id", name="patient_id_index")
    await reminders_collection.create_index("reminder_type", name="reminder_type_index")
    await reminders_collection.create_index("status", name="status_index")
    await reminders_collection.create_index("scheduled_time", name="scheduled_time_index")
    logger.info("Created reminders collection indexes")

    # notifications collection
    notifications_collection = database.notifications
    await notifications_collection.create_index("user_id", name="user_id_index")
    await notifications_collection.create_index("read", name="read_index")
    await notifications_collection.create_index("priority", name="priority_index")
    await notifications_collection.create_index("created_at", name="created_at_index")
    logger.info("Created notifications collection indexes")

    # notification_preferences collection
    notification_preferences_collection = database.notification_preferences
    await notification_preferences_collection.create_index("user_id", unique=True, name="user_id_unique")
    logger.info("Created notification_preferences collection indexes")

    # chat_sessions collection
    chat_sessions_collection = database.chat_sessions
    await chat_sessions_collection.create_index("patient_id", name="patient_id_index")
    await chat_sessions_collection.create_index("session_type", name="session_type_index")
    await chat_sessions_collection.create_index("active", name="active_index")
    await chat_sessions_collection.create_index("last_message_at", name="last_message_at_index")
    logger.info("Created chat_sessions collection indexes")

    # chat_messages collection
    chat_messages_collection = database.chat_messages
    await chat_messages_collection.create_index("session_id", name="session_id_index")
    await chat_messages_collection.create_index("sender_type", name="sender_type_index")
    await chat_messages_collection.create_index("created_at", name="created_at_index")
    logger.info("Created chat_messages collection indexes")

    # payments collection
    payments_collection = database.payments
    await payments_collection.create_index("appointment_id", name="appointment_id_index")
    await payments_collection.create_index("patient_id", name="patient_id_index")
    await payments_collection.create_index("doctor_id", name="doctor_id_index")
    await payments_collection.create_index("payment_status", name="payment_status_index")
    logger.info("Created payments collection indexes")

    # doctor_wallets collection
    doctor_wallets_collection = database.doctor_wallets
    await doctor_wallets_collection.create_index("doctor_id", unique=True, name="doctor_id_unique")
    logger.info("Created doctor_wallets collection indexes")

    # agent_logs collection
    agent_logs_collection = database.agent_logs
    await agent_logs_collection.create_index("agent_name", name="agent_name_index")
    await agent_logs_collection.create_index("workflow_id", name="workflow_id_index")
    await agent_logs_collection.create_index("session_id", name="session_id_index")
    await agent_logs_collection.create_index("status", name="status_index")
    await agent_logs_collection.create_index("created_at", name="created_at_index")
    logger.info("Created agent_logs collection indexes")

    # audit_logs collection
    audit_logs_collection = database.audit_logs
    await audit_logs_collection.create_index("user_id", name="user_id_index")
    await audit_logs_collection.create_index("action", name="action_index")
    await audit_logs_collection.create_index("resource_type", name="resource_type_index")
    await audit_logs_collection.create_index("created_at", name="created_at_index")
    logger.info("Created audit_logs collection indexes")
    
    # patient_memory collection
    patient_memory_collection = database.patient_memory
    await patient_memory_collection.create_index("patient_id", unique=True, name="patient_id_unique")
    await patient_memory_collection.create_index("last_updated", name="last_updated_index")
    logger.info("Created patient_memory collection indexes")
    
    # drug_master collection
    drug_master_collection = database.drug_master
    await drug_master_collection.create_index("normalized_name", unique=True, name="normalized_name_unique")
    await drug_master_collection.create_index("aliases", name="aliases_index")
    logger.info("Created drug_master collection indexes")
    
    logger.info("Database setup completed")