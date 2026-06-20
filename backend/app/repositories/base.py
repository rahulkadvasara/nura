"""
Nura - Base Repository
Base class for MongoDB repositories using Motor async driver
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel


ModelType = TypeVar("ModelType", bound=BaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def _to_model(model_class: type, doc: dict) -> Any:
    """Instantiate a model from a MongoDB document.

    If the model exposes a ``from_mongo`` classmethod (which handles
    ObjectId → str conversion) we use that; otherwise we fall back to
    the plain constructor.
    """
    if hasattr(model_class, "from_mongo"):
        return model_class.from_mongo(doc)
    return model_class(**doc)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with common async CRUD operations."""

    def __init__(self, collection: AsyncIOMotorCollection, model_class: type[ModelType]):
        self.collection = collection
        self.model_class = model_class

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Insert a new document and return the created model."""
        obj_dict = obj_in.model_dump(exclude_unset=True)
        result = await self.collection.insert_one(obj_dict)
        created_doc = await self.collection.find_one({"_id": result.inserted_id})
        if created_doc is None:
            raise RuntimeError("Document was inserted but could not be retrieved")
        return _to_model(self.model_class, created_doc)

    async def update(self, id: str, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """Update a document by ID and return the updated model."""
        update_data = obj_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get(id)

        update_data.setdefault("updated_at", self._now())

        result = await self.collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": update_data},
        )
        if result.modified_count:
            return await self.get(id)
        return None

    async def delete(self, id: str) -> bool:
        """Delete a document by ID. Returns True if a document was deleted."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(id)})
            return result.deleted_count > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, id: str) -> Optional[ModelType]:
        """Fetch a single document by its string ID."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(id)})
            if doc:
                return _to_model(self.model_class, doc)
        except Exception:
            pass
        return None

    async def get_by_filter(self, filter_dict: Dict[str, Any]) -> Optional[ModelType]:
        """Fetch the first document matching *filter_dict*."""
        doc = await self.collection.find_one(filter_dict)
        if doc:
            return _to_model(self.model_class, doc)
        return None

    async def get_many(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        skip: int = 0,
    ) -> List[ModelType]:
        """Fetch multiple documents matching *filter_dict*."""
        cursor = self.collection.find(filter_dict or {}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [_to_model(self.model_class, doc) for doc in docs]

    # ------------------------------------------------------------------
    # Aggregates
    # ------------------------------------------------------------------

    async def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count documents matching *filter_dict*."""
        return await self.collection.count_documents(filter_dict or {})

    async def exists(self, filter_dict: Dict[str, Any]) -> bool:
        """Return True if at least one document matches *filter_dict*."""
        count = await self.collection.count_documents(filter_dict, limit=1)
        return count > 0
