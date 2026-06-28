import os
import sys
import csv
import glob
from datetime import datetime, timezone
from pymongo import MongoClient

# Add project root to sys.path to import normalization and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.normalize_drug_names import normalize_drug_name

try:
    from backend.app.core.config import settings
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
    from app.core.config import settings

# Import index rebuilder
from scripts.rebuild_drug_indexes import rebuild_indexes

SEVERITY_MAP = {
    "minor": "LOW",
    "moderate": "MEDIUM",
    "major": "HIGH",
    "unknown": "UNKNOWN"
}

def import_ddinter():
    """Streams and processes DDInter CSV files sequentially and inserts them into MongoDB."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ddinter")
    csv_pattern = os.path.join(data_dir, "ddinter_downloads_code_*.csv")
    csv_files = glob.glob(csv_pattern)
    
    if not csv_files:
        print(f"Error: No CSV files found matching {csv_pattern}")
        sys.exit(1)
        
    print(f"Found {len(csv_files)} CSV files to import.")
    
    # Connect to MongoDB
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    # Drop collection for clean reload (ensures idempotency and fast bulk insert without indexing overhead)
    print("Dropping existing 'drug_interactions' collection...")
    db.drop_collection("drug_interactions")
    collection = db["drug_interactions"]
    
    batch_size = 5000
    batch = []
    total_rows_processed = 0
    total_records_inserted = 0
    malformed_rows_count = 0
    
    # In-memory deduplication set: stores (drug_a_normalized, drug_b_normalized)
    seen_pairs = set()
    imported_at = datetime.now(timezone.utc)
    
    for csv_file in sorted(csv_files):
        filename = os.path.basename(csv_file)
        print(f"Processing {filename}...")
        
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            
            # Read header
            try:
                header = next(reader)
                # Check column headers (case insensitive)
                header_lower = [h.lower() for h in header]
                if "drug_a" not in header_lower or "drug_b" not in header_lower:
                    print(f"Warning: Skipping {filename} - invalid header structure: {header}")
                    continue
                
                # Map column indices
                idx_drug_a = header_lower.index("drug_a")
                idx_drug_b = header_lower.index("drug_b")
                idx_level = header_lower.index("level") if "level" in header_lower else -1
            except StopIteration:
                print(f"Warning: Skipping empty file {filename}")
                continue
            
            for row in reader:
                total_rows_processed += 1
                
                # Basic validation
                if len(row) <= max(idx_drug_a, idx_drug_b):
                    malformed_rows_count += 1
                    continue
                
                raw_drug_a = row[idx_drug_a].strip()
                raw_drug_b = row[idx_drug_b].strip()
                
                if not raw_drug_a or not raw_drug_b:
                    malformed_rows_count += 1
                    continue
                
                # Normalize drug names
                norm_a = normalize_drug_name(raw_drug_a)
                norm_b = normalize_drug_name(raw_drug_b)
                
                # Skip self-interactions or normalization issues
                if not norm_a or not norm_b or norm_a == norm_b:
                    malformed_rows_count += 1
                    continue
                
                # Severity normalization
                raw_level = row[idx_level].strip().lower() if idx_level != -1 else "unknown"
                severity = SEVERITY_MAP.get(raw_level, "UNKNOWN")
                
                # Helper function to queue document for insert
                def queue_document(da, da_raw, db_name, db_raw):
                    nonlocal total_records_inserted
                    pair_key = (da, db_name)
                    if pair_key in seen_pairs:
                        return
                    
                    seen_pairs.add(pair_key)
                    
                    doc = {
                        "interaction_id": f"{da}__{db_name}",
                        "drug_a": da_raw,
                        "drug_a_normalized": da,
                        "drug_b": db_raw,
                        "drug_b_normalized": db_name,
                        "severity": severity,
                        "source_dataset": "ddinter",
                        "dataset_version": "1.0",
                        "imported_at": imported_at,
                        "aliases_a": [],
                        "aliases_b": [],
                        "interaction_description": f"Potential {severity.lower()} severity interaction between {da_raw} and {db_raw}."
                    }
                    batch.append(doc)
                    total_records_inserted += 1
                    
                    # Flush batch if full
                    if len(batch) >= batch_size:
                        collection.insert_many(batch)
                        batch.clear()
                
                # Insert bidirectional records
                # 1. Drug A -> Drug B
                queue_document(norm_a, raw_drug_a, norm_b, raw_drug_b)
                # 2. Drug B -> Drug A
                queue_document(norm_b, raw_drug_b, norm_a, raw_drug_a)
                
    # Insert remaining records in final batch
    if batch:
        collection.insert_many(batch)
        batch.clear()
        
    print("\nImport Statistics:")
    print(f"  Total CSV rows processed: {total_rows_processed}")
    print(f"  Malformed/invalid rows skipped: {malformed_rows_count}")
    print(f"  Deduplicated bidirectional records inserted: {total_records_inserted}")
    
    # Rebuild indexes
    print("")
    rebuild_indexes()
    
    client.close()
    print("\nImport pipeline completed successfully!")

if __name__ == "__main__":
    import_ddinter()
