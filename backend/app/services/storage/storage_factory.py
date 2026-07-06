import logging
from app.core.config import settings
from app.services.storage.storage_provider import StorageProvider
from app.services.storage.local_storage import LocalStorage
from app.services.storage.supabase_storage import SupabaseStorage

logger = logging.getLogger("nura.storage.factory")

_storage_provider = None

def get_storage_provider() -> StorageProvider:
    """Instantiate and return the configured active StorageProvider singleton."""
    global _storage_provider
    if _storage_provider is not None:
        return _storage_provider

    provider_name = settings.STORAGE_PROVIDER.lower().strip()
    logger.info(f"Initializing storage provider: {provider_name.upper()}")

    if provider_name == "supabase":
        try:
            _storage_provider = SupabaseStorage()
        except Exception as e:
            logger.error(f"Failed to initialize SupabaseStorage: {e}. Falling back to LocalStorage.")
            _storage_provider = LocalStorage()
    else:
        _storage_provider = LocalStorage()

    return _storage_provider
