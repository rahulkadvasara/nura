"""
Nura - Database Package
Database connection managers and initialization
"""

from app.db.mongodb import (
    MongoDBConnection,
    mongodb_connection,
    connect_to_mongodb,
    close_mongodb_connection,
    get_database,
    get_connection_status
)

from app.db.qdrant import (
    QdrantConnection,
    qdrant_connection,
    connect_to_qdrant,
    close_qdrant_connection,
    get_qdrant_client,
    get_qdrant_status
)

from app.db.init import setup_database

__all__ = [
    # MongoDB
    "MongoDBConnection",
    "mongodb_connection",
    "connect_to_mongodb",
    "close_mongodb_connection",
    "get_database",
    "get_connection_status",
    
    # Qdrant
    "QdrantConnection",
    "qdrant_connection",
    "connect_to_qdrant",
    "close_qdrant_connection",
    "get_qdrant_client",
    "get_qdrant_status",
    
    # Initialization
    "setup_database",
]