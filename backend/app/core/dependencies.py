"""
Nura - Dependencies
Dependency injection for services and repositories
"""

from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_database
from app.repositories import UserRepository, RefreshTokenRepository, OTPRepository
from app.services import UserService, AuthService, OTPService, EmailService


def get_user_repository() -> UserRepository:
    """Get UserRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return UserRepository(database.users)


def get_refresh_token_repository() -> RefreshTokenRepository:
    """Get RefreshTokenRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return RefreshTokenRepository(database.refresh_tokens)


def get_otp_repository() -> OTPRepository:
    """Get OTPRepository instance"""
    database: AsyncIOMotorDatabase = get_database()
    return OTPRepository(database.otp_verifications)


def get_user_service() -> UserService:
    """Get UserService instance"""
    user_repository = get_user_repository()
    return UserService(user_repository)


def get_auth_service() -> AuthService:
    """Get AuthService instance"""
    user_service = get_user_service()
    refresh_token_repository = get_refresh_token_repository()
    return AuthService(user_service, refresh_token_repository)


def get_otp_service() -> OTPService:
    """Get OTPService instance"""
    otp_repository = get_otp_repository()
    return OTPService(otp_repository)


def get_email_service() -> EmailService:
    """Get EmailService instance"""
    return EmailService()