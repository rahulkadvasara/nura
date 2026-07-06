import asyncio
import os
import sys
import logging
import mimetypes

# Add backend directory to python import paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.storage.supabase_storage import SupabaseStorage

# Set up logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("storage_migration")

async def migrate():
    logger.info("Starting local storage to Supabase migration...")
    
    # 1. Initialize Supabase Storage
    try:
        supabase_storage = SupabaseStorage()
    except Exception as e:
        logger.error(f"Failed to initialize Supabase Storage provider: {e}")
        return
        
    # 2. Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # --- MIGRATE AVATARS ---
    logger.info("Checking users for local avatars...")
    user_cursor = db.users.find({
        "profile_picture": {"$regex": "uploads/avatars/"}
    })
    
    users_migrated = 0
    users_failed = 0
    
    async for user in user_cursor:
        user_id = str(user["_id"])
        local_url = user["profile_picture"]
        logger.info(f"User {user_id}: found local avatar URL: {local_url}")
        
        # Parse the filename from URL
        filename = local_url.split("/uploads/avatars/")[-1]
        
        # Test candidate file paths
        candidate_paths = [
            os.path.join("uploads", "avatars", filename),
            os.path.join("backend", "uploads", "avatars", filename),
            os.path.join("..", "uploads", "avatars", filename),
        ]
        
        local_path = None
        for p in candidate_paths:
            if os.path.exists(p) and os.path.isfile(p):
                local_path = p
                break
                
        if not local_path:
            logger.warning(f"Local avatar file not found on disk for user {user_id}: searched {filename}")
            users_failed += 1
            continue
            
        try:
            # Check if file already exists in Supabase bucket to ensure idempotency
            exists = await supabase_storage.exists(bucket="avatars", object_key=filename)
            if exists:
                logger.info(f"Avatar file {filename} already exists on Supabase. Updating DB references only.")
                public_url = supabase_storage.get_public_url(bucket="avatars", object_key=filename)
                upload_res = {
                    "provider": "supabase",
                    "bucket": "avatars",
                    "object_key": filename,
                    "public_url": public_url,
                    "content_type": mimetypes.guess_type(local_path)[0] or "image/png",
                    "size": os.path.getsize(local_path)
                }
            else:
                # Upload to Supabase
                with open(local_path, "rb") as f:
                    content_type = mimetypes.guess_type(local_path)[0]
                    upload_res = await supabase_storage.upload_file(
                        file=f,
                        filename=filename,
                        bucket="avatars",
                        content_type=content_type
                    )
            
            # Update user record in MongoDB
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "profile_picture": upload_res["public_url"],
                    "profile_picture_metadata": upload_res
                }}
            )
            logger.info(f"User {user_id} avatar migrated successfully: {upload_res['public_url']}")
            users_migrated += 1
        except Exception as e:
            logger.error(f"Failed to migrate avatar for user {user_id}: {e}")
            users_failed += 1
            
    # --- MIGRATE REPORTS ---
    logger.info("Checking reports for local files...")
    # Find reports where file_url does not start with http/https
    report_cursor = db.reports.find({
        "file_url": {"$not": {"$regex": "^https?://"}}
    })
    
    reports_migrated = 0
    reports_failed = 0
    
    async for report in report_cursor:
        report_id = str(report["_id"])
        raw_file_url = report["file_url"]
        logger.info(f"Report {report_id}: found local file path entry: {raw_file_url}")
        
        filename = os.path.basename(raw_file_url)
        
        # Test candidate file paths
        candidate_paths = [
            raw_file_url,
            os.path.join("uploads", "reports", filename),
            os.path.join("backend", "uploads", "reports", filename),
            os.path.join("..", "uploads", "reports", filename),
        ]
        
        local_path = None
        for p in candidate_paths:
            if os.path.exists(p) and os.path.isfile(p):
                local_path = p
                break
            
        if not local_path:
            logger.warning(f"Local report file not found on disk for report {report_id}: searched {filename}")
            reports_failed += 1
            continue
            
        try:
            # Check if file already exists in Supabase bucket to ensure idempotency
            exists = await supabase_storage.exists(bucket="reports", object_key=filename)
            if exists:
                logger.info(f"Report file {filename} already exists on Supabase. Updating DB references only.")
                public_url = supabase_storage.get_public_url(bucket="reports", object_key=filename)
                upload_res = {
                    "provider": "supabase",
                    "bucket": "reports",
                    "object_key": filename,
                    "public_url": public_url,
                    "content_type": mimetypes.guess_type(local_path)[0] or "application/pdf",
                    "size": os.path.getsize(local_path)
                }
            else:
                # Upload to Supabase
                with open(local_path, "rb") as f:
                    content_type = mimetypes.guess_type(local_path)[0]
                    upload_res = await supabase_storage.upload_file(
                        file=f,
                        filename=filename,
                        bucket="reports",
                        content_type=content_type
                    )
            
            # Update report record in MongoDB
            await db.reports.update_one(
                {"_id": report["_id"]},
                {"$set": {
                    "file_url": upload_res["public_url"],
                    "file_metadata": upload_res
                }}
            )
            logger.info(f"Report {report_id} migrated successfully: {upload_res['public_url']}")
            reports_migrated += 1
        except Exception as e:
            logger.error(f"Failed to migrate report {report_id}: {e}")
            reports_failed += 1

    logger.info("=== Migration Completed ===")
    logger.info(f"Users migrated: {users_migrated}, Failed/Skipped: {users_failed}")
    logger.info(f"Reports migrated: {reports_migrated}, Failed/Skipped: {reports_failed}")

if __name__ == "__main__":
    asyncio.run(migrate())
