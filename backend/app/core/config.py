"""
Nura - Application Configuration
Using simplified environment variable loading with working database connections
"""

import os
from typing import List
from functools import lru_cache


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Load .env file if it exists
        self._load_env_file()
        
        # Application
        self.APP_NAME = os.getenv("APP_NAME", "Nura")
        self.APP_ENV = os.getenv("APP_ENV", "development")
        self.API_V1_PREFIX = os.getenv("API_V1_PREFIX", "/api/v1")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Security
        self.SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
        self.JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Frontend Communication
        self.FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # CORS Origins - handle as string and convert to list
        cors_origins = os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000")
        if isinstance(cors_origins, str):
            self.BACKEND_CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]
        else:
            self.BACKEND_CORS_ORIGINS = ["http://localhost:3000"]
        
        # MongoDB - Keep existing environment variable names
        self.MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/nura")
        self.MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "nura")
        
        # Qdrant
        self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
        self.CLUSTER_ID = os.getenv("CLUSTER_ID", "")
        
        # Groq AI
        self.GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
        self.DEFAULT_LLM = os.getenv("DEFAULT_LLM", "llama-3.3-70b-versatile")
        
        # Embedding Model
        self.EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        
        # Google OAuth
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        
        # Email Service (SMTP)
        self.SMTP_HOST = os.getenv("SMTP_HOST", "")
        self.SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        self.SMTP_USER = os.getenv("SMTP_USER", "")
        self.SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
        
        # Supabase Storage
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
        self.SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        self.SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "medical-files")
        
        # Razorpay Payment Gateway
        self.RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
        self.RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
        
        # Upload Limits
        self.MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))

        # Admin Bootstrap Configuration
        self.ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
        self.ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
        self.ADMIN_NAME = os.getenv("ADMIN_NAME", "")
    
    def _load_env_file(self):
        """Load .env file if it exists"""
        try:
            from dotenv import load_dotenv
            load_dotenv(".env")
        except ImportError:
            # dotenv not available, skip
            pass
        except Exception:
            # .env file not found or error loading, skip
            pass


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()


# Create global settings instance
settings = get_settings()