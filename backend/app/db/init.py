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
    
    logger.info("Database setup completed")