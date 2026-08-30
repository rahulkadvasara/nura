"""
Nura - Vector Service
Service for indexing, searching, and managing high-dimensional vector embeddings inside Qdrant.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.models import PointStruct

from app.core.ai_config import AISettings, ai_settings
from app.core.exceptions import AIConfigurationError
from app.services.vector_collection_service import VectorCollectionService, get_vector_collection_service

logger = logging.getLogger("nura.ai.vector")


class VectorService:
    """Core Vector service for low-level Qdrant CRUD and semantic search operations"""
    
    def __init__(
        self,
        client: Optional[QdrantClient] = None,
        collection_service: Optional[VectorCollectionService] = None,
        settings: AISettings = ai_settings
    ):
        self.settings = settings
        try:
            self.settings.validate_config()
        except AIConfigurationError as e:
            logger.warning(f"VectorService config unvalidated: {e}")
        self._client = client
        self._collection_service = collection_service


    @property
    def client(self) -> QdrantClient:
        """Lazy load Qdrant client instance from global connection manager"""
        if self._client is None:
            from app.db.qdrant import get_qdrant_client
            self._client = get_qdrant_client()
        return self._client

    @property
    def collection_service(self) -> VectorCollectionService:
        """Lazy load VectorCollectionService instance"""
        if self._collection_service is None:
            self._collection_service = get_vector_collection_service()
        return self._collection_service

    def parse_date_to_epoch(self, val: Any) -> Any:
        """Helper to parse dates (datetime or ISO string) to UTC epoch float for Qdrant Range compatibility"""
        from datetime import datetime, timezone
        if isinstance(val, str):
            try:
                # Standard ISO parser support
                clean_val = val
                if clean_val.endswith('Z'):
                    clean_val = clean_val[:-1] + '+00:00'
                dt = datetime.fromisoformat(clean_val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                try:
                    from dateutil import parser
                    dt = parser.parse(val)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.timestamp()
                except Exception:
                    return val
        elif isinstance(val, datetime):
            if val.tzinfo is None:
                val = val.replace(tzinfo=timezone.utc)
            return val.timestamp()
        return val

    def serialize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize datetime and date string fields in payloads to float epochs for range query matching"""
        serialized = {}
        for k, v in payload.items():
            if k in {"indexed_at", "created_at", "updated_at"}:
                serialized[k] = self.parse_date_to_epoch(v)
            else:
                serialized[k] = v
        return serialized

    def build_qdrant_filter(self, filter_dict: Optional[Dict[str, Any]]) -> Optional[qdrant_models.Filter]:
        """Convert a standard python dictionary of query parameters/operators into a Qdrant Filter object"""
        if not filter_dict:
            return None
        
        conditions = []
        for key, val in filter_dict.items():
            if val is None:
                continue
            
            # Operator filters (e.g. date ranges, contains, lists)
            if isinstance(val, dict):
                range_ops = {"$gte", "$lte", "$gt", "$lt"}
                if any(op in val for op in range_ops):
                    range_kwargs = {}
                    for op in range_ops:
                        if op in val:
                            range_kwargs[op[1:]] = self.parse_date_to_epoch(val[op])
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            range=qdrant_models.Range(**range_kwargs)
                        )
                    )
                elif "$eq" in val:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=val["$eq"])
                        )
                    )
                elif "$contains" in val:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=val["$contains"])
                        )
                    )
                elif "$in" in val:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchAny(any=val["$in"])
                        )
                    )
            # List parameters (e.g. match tags in list)
            elif isinstance(val, list):
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchAny(any=val)
                    )
                )
            # Standard exact matches
            else:
                conditions.append(
                    qdrant_models.FieldCondition(
                        key=key,
                        match=qdrant_models.MatchValue(value=val)
                    )
                )
                
        if not conditions:
            return None
            
        return qdrant_models.Filter(must=conditions)

    async def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        distance: Optional[str] = None
    ) -> bool:
        """Create a collection idempotently via the collection manager service"""
        return await self.collection_service.create_collection(
            name=collection_name,
            vector_size=vector_size,
            distance=distance
        )

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection via the collection manager service"""
        return await self.collection_service.delete_collection(name=collection_name)

    async def _handle_missing_collection_or_index(self, collection_name: str, error: Exception) -> bool:
        err_str = str(error)
        err_lower = err_str.lower()
        target_col = self.collection_service.get_collection_name(collection_name)
        
        # Dynamically extract specific missing field name from Qdrant error message if present
        import re
        match = re.search(r'Index required but not found for ["\\]+([^"\\]+)["\\]+', err_str, re.IGNORECASE)
        if match:
            missing_field = match.group(1)
            logger.info(f"Auto-creating missing Qdrant payload index for field '{missing_field}' in collection '{target_col}'")
            try:
                from qdrant_client.http import models as qdrant_models
                self.client.create_payload_index(
                    collection_name=target_col,
                    field_name=missing_field,
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD
                )
            except Exception as ex:
                logger.warning(f"Failed to create payload index for '{missing_field}': {ex}")
            self.collection_service.ensure_payload_indexes(collection_name)
            return True
        elif "index required" in err_lower or ("not found" in err_lower and "index" in err_lower):
            logger.info(f"Auto-creating payload indexes for Qdrant collection '{target_col}'")
            self.collection_service.ensure_payload_indexes(collection_name)
            return True
        elif "doesn't exist" in err_lower or ("collection" in err_lower and "not found" in err_lower):
            logger.info(f"Auto-creating missing Qdrant collection '{target_col}'")
            await self.create_collection(collection_name)
            return True
        return False

    async def upsert(self, collection_name: str, id: Union[str, int], vector: List[float], payload: Dict[str, Any]) -> bool:
        """Insert or update a single vector point in the database"""
        target_col = self.collection_service.get_collection_name(collection_name)
        try:
            logger.info(f"Upserting point {id} to collection {target_col}")
            serialized_payload = self.serialize_payload(payload)
            self.client.upsert(
                collection_name=target_col,
                points=[PointStruct(id=id, vector=vector, payload=serialized_payload)],
                wait=True
            )
            return True
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                self.client.upsert(
                    collection_name=target_col,
                    points=[PointStruct(id=id, vector=vector, payload=self.serialize_payload(payload))],
                    wait=True
                )
                return True
            logger.error(f"Failed to upsert vector point {id} to Qdrant collection '{target_col}': {e}")
            raise AIConfigurationError(f"Vector upsert failed: {str(e)}") from e

    async def upsert_batch(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Idempotently load lists of point items to Qdrant in sub-batches, executing automatic retries upon failure"""
        target_col = self.collection_service.get_collection_name(collection_name)
        target_batch_size = batch_size or self.settings.EMBEDDING_BATCH_SIZE
        
        success_ids = []
        failed_ids = []
        errors = []
        
        for i in range(0, len(points), target_batch_size):
            chunk = points[i:i + target_batch_size]
            qdrant_points = []
            chunk_ids = []
            for p in chunk:
                qdrant_points.append(
                    PointStruct(
                        id=p["id"],
                        vector=p["vector"],
                        payload=self.serialize_payload(p["payload"])
                    )
                )
                chunk_ids.append(p["id"])
                
            # Perform operations with a simple retry block
            retries = 3
            backoff = 0.5
            success = False
            last_err = ""
            
            while retries > 0 and not success:
                try:
                    self.client.upsert(
                        collection_name=target_col,
                        points=qdrant_points,
                        wait=True
                    )
                    success = True
                except Exception as e:
                    if retries == 3:
                        await self._handle_missing_collection_or_index(collection_name, e)
                    retries -= 1
                    last_err = str(e)
                    if retries > 0:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        
            if success:
                success_ids.extend(chunk_ids)
            else:
                failed_ids.extend(chunk_ids)
                errors.append(f"Failed upserting chunk starting at index {i}: {last_err}")
                
        return {
            "success": len(failed_ids) == 0,
            "processed_count": len(success_ids),
            "failed_count": len(failed_ids),
            "success_ids": success_ids,
            "failed_ids": failed_ids,
            "errors": errors
        }

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query nearest neighbor matches against a collection, supporting metadata filtering options (protected by circuit breaker)"""
        target_col = self.collection_service.get_collection_name(collection_name)
        qdrant_filter = self.build_qdrant_filter(filter_dict)

        from app.utils.circuit_breaker import get_circuit_breaker
        
        def fallback_search(*args, **kwargs) -> List[Dict[str, Any]]:
            logger.error(f"Qdrant vector search circuit breaker fallback triggered for '{target_col}'. Returning empty list.")
            return []

        cb = get_circuit_breaker("qdrant_service", fallback_func=fallback_search)

        def _do_qdrant_search(col: str):
            if hasattr(self.client, "search"):
                return self.client.search(
                    collection_name=col,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit
                )
            elif hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=col,
                    query=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit
                )
                return getattr(res, "points", [])
            else:
                return []

        async def do_search():
            try:
                logger.info(f"Searching nearest neighbors in collection {target_col} (limit: {limit})")
                results = _do_qdrant_search(target_col)
                return [
                    {
                        "id": str(r.id),
                        "score": float(getattr(r, "score", 0.0)),
                        "payload": getattr(r, "payload", {}) or {}
                    }
                    for r in results
                ]
            except Exception as e:
                err_msg = str(e)
                if "not found" in err_msg.lower() or "doesn't exist" in err_msg.lower():
                    logger.warning(f"Collection '{target_col}' not present. Returning empty search results.")
                    return []
                if await self._handle_missing_collection_or_index(collection_name, e):
                    results = _do_qdrant_search(target_col)
                    return [
                        {
                            "id": str(r.id),
                            "score": float(getattr(r, "score", 0.0)),
                            "payload": getattr(r, "payload", {}) or {}
                        }
                        for r in results
                    ]
                logger.error(f"Search query failed in collection '{target_col}': {e}")
                raise AIConfigurationError(f"Vector search failed: {str(e)}") from e

        return await cb.execute_async(do_search)


    async def delete(self, collection_name: str, ids: List[Union[str, int]]) -> bool:
        """Delete specific vector point records by ID"""
        target_col = self.collection_service.get_collection_name(collection_name)
        try:
            self.client.delete(
                collection_name=target_col,
                points_selector=qdrant_models.PointIdsList(points=ids)
            )
            return True
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                self.client.delete(
                    collection_name=target_col,
                    points_selector=qdrant_models.PointIdsList(points=ids)
                )
                return True
            logger.error(f"Delete points failed in collection '{target_col}': {e}")
            raise AIConfigurationError(f"Vector points deletion failed: {str(e)}") from e

    async def delete_by_filter(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete all points that match a metadata filter criteria"""
        target_col = self.collection_service.get_collection_name(collection_name)
        qdrant_filter = self.build_qdrant_filter(filter_dict)
        try:
            if not qdrant_filter:
                raise ValueError("Must provide filter parameters to delete_by_filter")
            self.client.delete(
                collection_name=target_col,
                points_selector=qdrant_models.FilterSelector(filter=qdrant_filter)
            )
            return True
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                self.client.delete(
                    collection_name=target_col,
                    points_selector=qdrant_models.FilterSelector(filter=qdrant_filter)
                )
                return True
            logger.error(f"Delete by filter failed in collection '{target_col}': {e}")
            raise AIConfigurationError(f"Vector delete by filter failed: {str(e)}") from e

    async def get(self, collection_name: str, ids: List[Union[str, int]]) -> List[Dict[str, Any]]:
        """Retrieve point vector and payload details directly by ID"""
        target_col = self.collection_service.get_collection_name(collection_name)
        try:
            results = self.client.retrieve(
                collection_name=target_col,
                ids=ids,
                with_payload=True,
                with_vectors=True
            )
            return [
                {
                    "id": str(r.id),
                    "payload": r.payload or {},
                    "vector": r.vector
                }
                for r in results
            ]
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                results = self.client.retrieve(
                    collection_name=target_col,
                    ids=ids,
                    with_payload=True,
                    with_vectors=True
                )
                return [
                    {
                        "id": str(r.id),
                        "payload": r.payload or {},
                        "vector": r.vector
                    }
                    for r in results
                ]
            logger.error(f"Points retrieve failed in collection '{target_col}': {e}")
            raise AIConfigurationError(f"Vector retrieve failed: {str(e)}") from e

    async def count(self, collection_name: str, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count the number of points in a collection matching an optional filter"""
        target_col = self.collection_service.get_collection_name(collection_name)
        qdrant_filter = self.build_qdrant_filter(filter_dict)
        try:
            res = self.client.count(
                collection_name=target_col,
                count_filter=qdrant_filter,
                exact=True
            )
            return res.count
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                res = self.client.count(
                    collection_name=target_col,
                    count_filter=qdrant_filter,
                    exact=True
                )
                return res.count
            logger.error(f"Vector count failed in collection '{target_col}': {e}")
            raise AIConfigurationError(f"Vector count query failed: {str(e)}") from e

    async def scroll(
        self,
        collection_name: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: Optional[Any] = None
    ) -> tuple:
        """Paginate through vector records list using Qdrant scroll offsets"""
        target_col = self.collection_service.get_collection_name(collection_name)
        qdrant_filter = self.build_qdrant_filter(filter_dict)
        try:
            points, next_offset = self.client.scroll(
                collection_name=target_col,
                scroll_filter=qdrant_filter,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=True
            )
            points_list = [
                {
                    "id": str(p.id),
                    "payload": p.payload or {},
                    "vector": p.vector
                }
                for p in points
            ]
            return points_list, next_offset
        except Exception as e:
            if await self._handle_missing_collection_or_index(collection_name, e):
                try:
                    points, next_offset = self.client.scroll(
                        collection_name=target_col,
                        scroll_filter=qdrant_filter,
                        limit=limit,
                        offset=offset,
                        with_payload=True,
                        with_vectors=True
                    )
                    points_list = [
                        {
                            "id": str(p.id),
                            "payload": p.payload or {},
                            "vector": p.vector
                        }
                        for p in points
                    ]
                    return points_list, next_offset
                except Exception as retry_err:
                    logger.warning(f"Qdrant scroll retry failed after index creation: {retry_err}")
                    return [], None
            logger.warning(f"Qdrant scroll query failed in collection '{target_col}': {e}")
            return [], None

    async def health(self) -> dict:
        """Ping check details of the vector store connection status"""
        return await self.collection_service.health_check()


# Singleton reference cache
_vector_service_instance: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Retrieve singleton instance of VectorService"""
    global _vector_service_instance
    if _vector_service_instance is None:
        _vector_service_instance = VectorService()
    return _vector_service_instance
