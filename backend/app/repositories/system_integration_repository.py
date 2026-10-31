"""
Nura - System Integration Repository
MongoDB repository for storing system-wide integrations and OAuth tokens (e.g. Google Meet)
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorCollection


class SystemIntegrationRepository:
    """Repository for managing system integrations (OAuth tokens, API settings)"""

    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def get_integration(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve integration document by name (e.g., 'google_meet')"""
        try:
            return await self.collection.find_one({"name": name})
        except Exception:
            return None

    async def save_integration(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update integration document by name"""
        now = self._now()
        data_to_save = dict(data)
        data_to_save["name"] = name
        data_to_save["updated_at"] = now
        # Remove created_at from $set dictionary to prevent conflict with $setOnInsert
        data_to_save.pop("created_at", None)

        await self.collection.update_one(
            {"name": name},
            {
                "$set": data_to_save,
                "$setOnInsert": {"created_at": now}
            },
            upsert=True
        )
        updated = await self.get_integration(name)
        return updated or data_to_save

