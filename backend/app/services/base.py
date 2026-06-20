"""
Nura - Base Service
Base class for service layer
"""

from typing import Optional, TypeVar, Generic
from pydantic import BaseModel


ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base service with common operations"""
    
    def __init__(self):
        pass
    
    async def validate_input(self, data: CreateSchemaType) -> Optional[dict]:
        """Validate input data (to be overridden by subclasses)"""
        return data.dict(exclude_unset=True) if data else None
    
    def prepare_response(self, model: ModelType) -> dict:
        """Prepare model for response (to be overridden by subclasses)"""
        return model.dict() if model else {}