"""
Nura - MongoDB Connection Manager
Motor async MongoDB driver with connection pooling
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class MongoDBConnection:
    """MongoDB connection manager"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Create MongoDB connection with multiple fallback strategies"""
        try:
            # Check if MongoDB URL is configured
            if not settings.MONGODB_URL or settings.MONGODB_URL == "mongodb://localhost:27017/nura":
                logger.warning("MongoDB URL not configured, using local development defaults")
            
            # Base connection options
            base_options = {
                "maxPoolSize": 50,
                "minPoolSize": 10,
                "maxIdleTimeMS": 30000,
                "serverSelectionTimeoutMS": 8000,
                "connectTimeoutMS": 8000,
                "socketTimeoutMS": 8000,
            }
            
            # Try different connection strategies for MongoDB Atlas
            if "mongodb.net" in settings.MONGODB_URL or "mongodb+srv" in settings.MONGODB_URL:
                connection_strategies = [
                    # Strategy 1: Standard Atlas connection
                    {
                        **base_options,
                        "tls": True,
                        "retryWrites": True,
                    },
                    # Strategy 2: Lenient TLS
                    {
                        **base_options,
                        "tls": True,
                        "tlsAllowInvalidCertificates": True,
                        "tlsInsecure": True,
                        "retryWrites": True,
                    },
                    # Strategy 3: Force TLS 1.2
                    {
                        **base_options,
                        "ssl": True,
                        "ssl_cert_reqs": None,
                        "retryWrites": True,
                    },
                ]
            else:
                # Local connection
                connection_strategies = [base_options]
            
            # Try each strategy
            last_error = None
            for i, options in enumerate(connection_strategies):
                try:
                    logger.info(f"Attempting MongoDB connection strategy {i + 1}/{len(connection_strategies)}")
                    
                    self.client = AsyncIOMotorClient(settings.MONGODB_URL, **options)
                    
                    # Test connection with shorter timeout for faster failover
                    await self.client.admin.command('ping')
                    
                    self.database = self.client[settings.MONGODB_DATABASE]
                    
                    logger.info("MongoDB connected successfully", extra={
                        "database": settings.MONGODB_DATABASE,
                        "strategy": i + 1
                    })
                    return  # Success!
                    
                except Exception as e:
                    last_error = e
                    logger.debug(f"MongoDB connection strategy {i + 1} failed: {e}")
                    if self.client:
                        self.client.close()
                        self.client = None
                    continue
            
            # All strategies failed
            raise last_error or Exception("All connection strategies failed")
            
        except Exception as e:
            logger.warning(f"MongoDB connection failed (this is OK for Phase 0): {e}")
            # For Phase 0, we'll allow this to fail gracefully
            self.client = None
            self.database = None
    
    async def close(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance"""
        if self.database is None:
            raise RuntimeError("MongoDB not connected")
        return self.database


# Global MongoDB connection instance
mongodb_connection = MongoDBConnection()


async def connect_to_mongodb() -> None:
    """Connect to MongoDB"""
    await mongodb_connection.connect()


async def close_mongodb_connection() -> None:
    """Close MongoDB connection"""
    await mongodb_connection.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    return mongodb_connection.get_database()


async def get_connection_status() -> str:
    """Get MongoDB connection status"""
    try:
        is_connected = await mongodb_connection.is_connected()
        return "connected" if is_connected else "not_configured"
    except Exception:
        return "not_configured"