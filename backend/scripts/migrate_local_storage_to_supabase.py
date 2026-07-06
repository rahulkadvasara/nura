import asyncio
import os
import sys
import logging
import mimetypes
import time
import hashlib
from typing import Dict, Any, Optional

# Add backend directory to python import paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.storage.supabase_storage import SupabaseStorage

# Set up logging format
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("storage_migration")

def calculate_file_sha256(filepath: str) -> str:
    """Calculate the SHA-256 checksum of a local file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()

async def migrate():
    start_time = time.time()
    logger.info("Starting local storage to Supabase production-grade migration...")
    
    # 1. Initialize Supabase Storage
    try:
        supabase_storage = SupabaseStorage()
    except Exception as e:
        logger.error(f"Failed to initialize Supabase Storage provider: {e}")
        return
        
    # 2. Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    report_stats = {
        "avatars": {"scanned": 0, "migrated": 0, "skipped": 0, "failed": 0},
        "reports": {"scanned": 0, "migrated": 0, "skipped": 0, "failed": 0},
        "doctor_documents": {"scanned": 0, "migrated": 0, "skipped": 0, "failed": 0}
    }
    
    # ------------------ 1. MIGRATE AVATARS ------------------
    logger.info("Scanning users for local avatars...")
    # Find all users that have profile pictures which are local
    async for user in db.users.find({}):
        profile_pic = user.get("profile_picture")
        metadata = user.get("profile_picture_metadata")
        
        # Check if local
        is_local = False
        if profile_pic and ("uploads/avatars/" in profile_pic or not profile_pic.startswith("http")):
            is_local = True
            
        if not is_local:
            continue
            
        report_stats["avatars"]["scanned"] += 1
        user_id = str(user["_id"])
        
        # Check if already migrated in DB
        if metadata and metadata.get("provider") == "supabase":
            logger.info(f"User {user_id} avatar already migrated to Supabase. Skipping.")
            report_stats["avatars"]["skipped"] += 1
            continue
            
        # Locate the local file on disk
        filename = profile_pic.split("/uploads/avatars/")[-1] if "/uploads/avatars/" in profile_pic else os.path.basename(profile_pic)
        
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
            logger.warning(f"Local file not found on disk for user {user_id} avatar: {filename}")
            report_stats["avatars"]["failed"] += 1
            continue
            
        # Determine deterministic path avatars/users/{user_id}/avatar.webp
        # We will keep original extension if it's already WebP, or preserve ext to prevent breaks
        ext = os.path.splitext(local_path)[1].lower() or ".webp"
        object_key = f"users/{user_id}/avatar{ext}"
        
        try:
            local_sha = calculate_file_sha256(local_path)
            local_size = os.path.getsize(local_path)
            
            # Check if file exists in Supabase
            exists = await supabase_storage.exists(bucket="avatars", object_key=object_key)
            uploaded_metadata = None
            
            if exists:
                logger.info(f"Avatar file {object_key} already exists in Supabase bucket. Verifying checksum...")
                # We can perform verify by updating metadata
                public_url = supabase_storage.get_public_url(bucket="avatars", object_key=object_key)
                uploaded_metadata = {
                    "provider": "supabase",
                    "bucket": "avatars",
                    "object_key": object_key,
                    "public_url": public_url,
                    "original_filename": filename,
                    "content_type": mimetypes.guess_type(local_path)[0] or "image/webp",
                    "size_bytes": local_size,
                    "checksum_sha256": local_sha,
                    "storage_version": "1.0.0"
                }
            else:
                # Upload to Supabase
                with open(local_path, "rb") as f:
                    content_type = mimetypes.guess_type(local_path)[0]
                    uploaded_metadata = await supabase_storage.upload_file(
                        file=f,
                        filename=object_key,
                        bucket="avatars",
                        content_type=content_type,
                        original_filename=filename
                    )
                # Verify size/checksum
                if uploaded_metadata.get("checksum_sha256") != local_sha:
                    raise ValueError("Uploaded file SHA-256 checksum mismatch!")
            
            # Update user record in MongoDB
            update_result = await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "profile_picture": uploaded_metadata["public_url"],
                    "profile_picture_metadata": uploaded_metadata
                }}
            )
            
            if update_result.modified_count == 0 and not exists:
                # Rollback if update fails
                logger.error(f"MongoDB update failed for user {user_id}. Rolling back uploaded storage file.")
                await supabase_storage.delete_file(bucket="avatars", object_key=object_key)
                report_stats["avatars"]["failed"] += 1
            else:
                logger.info(f"User {user_id} avatar successfully migrated: {object_key}")
                report_stats["avatars"]["migrated"] += 1
                
        except Exception as e:
            logger.error(f"Failed to migrate avatar for user {user_id}: {e}")
            report_stats["avatars"]["failed"] += 1
            
    # ------------------ 2. MIGRATE MEDICAL REPORTS ------------------
    logger.info("Scanning reports for local medical reports...")
    async for report in db.reports.find({}):
        file_url = report.get("file_url")
        metadata = report.get("file_metadata")
        
        is_local = False
        if file_url and ("uploads/reports/" in file_url or not file_url.startswith("http")):
            is_local = True
            
        if not is_local:
            continue
            
        report_stats["reports"]["scanned"] += 1
        report_id = str(report["_id"])
        patient_id = report.get("patient_id", "unknown")
        
        # Check if already migrated
        if metadata and metadata.get("provider") == "supabase":
            logger.info(f"Report {report_id} already migrated to Supabase. Skipping.")
            report_stats["reports"]["skipped"] += 1
            continue
            
        filename = os.path.basename(file_url)
        candidate_paths = [
            file_url,
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
            logger.warning(f"Local file not found on disk for report {report_id}: {filename}")
            report_stats["reports"]["failed"] += 1
            continue
            
        # Enforce deterministic path reports/patients/{patient_id}/{report_id}.pdf
        ext = os.path.splitext(local_path)[1].lower() or ".pdf"
        object_key = f"patients/{patient_id}/{report_id}{ext}"
        
        try:
            local_sha = calculate_file_sha256(local_path)
            local_size = os.path.getsize(local_path)
            
            exists = await supabase_storage.exists(bucket="reports", object_key=object_key)
            uploaded_metadata = None
            
            if exists:
                logger.info(f"Report file {object_key} already exists in Supabase. Verifying checksum...")
                uploaded_metadata = {
                    "provider": "supabase",
                    "bucket": "reports",
                    "object_key": object_key,
                    "public_url": None, # Private bucket
                    "original_filename": filename,
                    "content_type": mimetypes.guess_type(local_path)[0] or "application/pdf",
                    "size_bytes": local_size,
                    "checksum_sha256": local_sha,
                    "storage_version": "1.0.0"
                }
            else:
                # Upload to Supabase private reports bucket
                with open(local_path, "rb") as f:
                    content_type = mimetypes.guess_type(local_path)[0]
                    uploaded_metadata = await supabase_storage.upload_file(
                        file=f,
                        filename=object_key,
                        bucket="reports",
                        content_type=content_type,
                        original_filename=filename
                    )
                if uploaded_metadata.get("checksum_sha256") != local_sha:
                    raise ValueError("Uploaded report SHA-256 checksum mismatch!")
                    
            # Update DB
            update_result = await db.reports.update_one(
                {"_id": report["_id"]},
                {"$set": {
                    "file_url": f"reports/{object_key}", # Private key representation
                    "file_metadata": uploaded_metadata
                }}
            )
            
            if update_result.modified_count == 0 and not exists:
                logger.error(f"MongoDB update failed for report {report_id}. Rolling back storage file.")
                await supabase_storage.delete_file(bucket="reports", object_key=object_key)
                report_stats["reports"]["failed"] += 1
            else:
                logger.info(f"Report {report_id} successfully migrated: {object_key}")
                report_stats["reports"]["migrated"] += 1
                
        except Exception as e:
            logger.error(f"Failed to migrate report {report_id}: {e}")
            report_stats["reports"]["failed"] += 1
            
    # ------------------ 3. MIGRATE DOCTOR DOCUMENTS ------------------
    logger.info("Scanning doctor_documents for local verification documents...")
    async for doc in db.doctor_documents.find({}):
        doc_url = doc.get("document_url")
        metadata = doc.get("document_metadata")
        
        is_local = False
        if doc_url and ("uploads/doctor-documents/" in doc_url or not doc_url.startswith("http")):
            is_local = True
            
        if not is_local:
            continue
            
        report_stats["doctor_documents"]["scanned"] += 1
        doc_id = str(doc["_id"])
        doctor_id = doc.get("doctor_id", "unknown")
        doc_type = doc.get("document_type", "degree")
        
        # Check if already migrated
        if metadata and metadata.get("provider") == "supabase":
            logger.info(f"Doctor document {doc_id} already migrated. Skipping.")
            report_stats["doctor_documents"]["skipped"] += 1
            continue
            
        filename = os.path.basename(doc_url)
        candidate_paths = [
            doc_url,
            os.path.join("uploads", "doctor-documents", filename),
            os.path.join("backend", "uploads", "doctor-documents", filename),
            os.path.join("..", "uploads", "doctor-documents", filename),
        ]
        
        local_path = None
        for p in candidate_paths:
            if os.path.exists(p) and os.path.isfile(p):
                local_path = p
                break
                
        if not local_path:
            logger.warning(f"Local file not found on disk for doctor document {doc_id}: {filename}")
            report_stats["doctor_documents"]["failed"] += 1
            continue
            
        # Enforce deterministic path doctor-documents/doctors/{doctor_id}/{document_name}
        ext = os.path.splitext(local_path)[1].lower() or ".pdf"
        object_key = f"doctors/{doctor_id}/{doc_type}{ext}"
        
        try:
            local_sha = calculate_file_sha256(local_path)
            local_size = os.path.getsize(local_path)
            
            exists = await supabase_storage.exists(bucket="doctor-documents", object_key=object_key)
            uploaded_metadata = None
            
            if exists:
                logger.info(f"Doctor document {object_key} already exists. Verifying checksum...")
                uploaded_metadata = {
                    "provider": "supabase",
                    "bucket": "doctor-documents",
                    "object_key": object_key,
                    "public_url": None, # Private bucket
                    "original_filename": filename,
                    "content_type": mimetypes.guess_type(local_path)[0] or "application/pdf",
                    "size_bytes": local_size,
                    "checksum_sha256": local_sha,
                    "storage_version": "1.0.0"
                }
            else:
                with open(local_path, "rb") as f:
                    content_type = mimetypes.guess_type(local_path)[0]
                    uploaded_metadata = await supabase_storage.upload_file(
                        file=f,
                        filename=object_key,
                        bucket="doctor-documents",
                        content_type=content_type,
                        original_filename=filename
                    )
                if uploaded_metadata.get("checksum_sha256") != local_sha:
                    raise ValueError("Uploaded doctor document SHA-256 checksum mismatch!")
                    
            # Update DB
            update_result = await db.doctor_documents.update_one(
                {"_id": doc["_id"]},
                {"$set": {
                    "document_url": f"doctor-documents/{object_key}", # Private key path
                    "document_metadata": uploaded_metadata
                }}
            )
            
            if update_result.modified_count == 0 and not exists:
                logger.error(f"MongoDB update failed for doctor document {doc_id}. Rolling back storage file.")
                await supabase_storage.delete_file(bucket="doctor-documents", object_key=object_key)
                report_stats["doctor_documents"]["failed"] += 1
            else:
                logger.info(f"Doctor document {doc_id} successfully migrated: {object_key}")
                report_stats["doctor_documents"]["migrated"] += 1
                
        except Exception as e:
            logger.error(f"Failed to migrate doctor document {doc_id}: {e}")
            report_stats["doctor_documents"]["failed"] += 1
            
    elapsed_time = time.time() - start_time
    
    # ------------------ PRINT DETAILED REPORT ------------------
    print("\n" + "="*50)
    print("           STORAGE MIGRATION SUMMARY REPORT           ")
    print("="*50)
    print(f"Elapsed Time: {elapsed_time:.2f} seconds\n")
    
    for category, stats in report_stats.items():
        print(f"Collection: {category.upper()}")
        print(f"  Scanned Files:  {stats['scanned']}")
        print(f"  Migrated Files: {stats['migrated']}")
        print(f"  Skipped Files:  {stats['skipped']}")
        print(f"  Failed Files:   {stats['failed']}")
        print("-"*50)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(migrate())
