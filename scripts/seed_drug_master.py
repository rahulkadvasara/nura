import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING

# Add project root to sys.path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Explicitly load .env from backend folder
try:
    from dotenv import load_dotenv
    backend_env = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")
    if os.path.exists(backend_env):
        load_dotenv(backend_env)
except ImportError:
    pass

try:
    from backend.app.core.config import settings
except ImportError:
    # If app path is different, adjust path addition
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
    from app.core.config import settings

def seed_drug_master():
    """Seeds the drug_master collection from unique entries in drug_interactions."""
    print(f"Connecting to MongoDB at: {settings.MONGODB_URL}")
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    
    interactions_col = db["drug_interactions"]
    master_col = db["drug_master"]
    
    # Check if already seeded
    existing_count = master_col.count_documents({})
    if existing_count > 0:
        print(f"drug_master already contains {existing_count} records. Skipping seeding.")
        client.close()
        return

    print("Grouping unique normalized drugs from 'drug_interactions'...")
    pipeline = [
        {
            "$project": {
                "drugs": [
                    {"name": "$drug_a", "normalized": "$drug_a_normalized"},
                    {"name": "$drug_b", "normalized": "$drug_b_normalized"}
                ]
            }
        },
        {"$unwind": "$drugs"},
        {
            "$group": {
                "_id": "$drugs.normalized",
                "raw_names": {"$addToSet": "$drugs.name"}
            }
        }
    ]
    
    groups = list(interactions_col.aggregate(pipeline))
    print(f"Found {len(groups)} unique normalized drugs.")
    
    if not groups:
        print("No drugs found in drug_interactions. Make sure the dataset is loaded first.")
        client.close()
        return
        
    documents = []
    now = datetime.now(timezone.utc)
    
    for g in groups:
        normalized_name = g["_id"]
        if not normalized_name:
            continue
            
        raw_names = g["raw_names"]
        # Find a suitable display name: pick the shortest or capitalized name
        raw_names_sorted = sorted(raw_names, key=len)
        canonical_name = raw_names_sorted[0] if raw_names_sorted else normalized_name
        
        # All raw names that are different from the canonical name can be aliases
        aliases = [name for name in raw_names if name.lower() != canonical_name.lower()]
        
        doc = {
            "drug_name": canonical_name,
            "normalized_name": normalized_name,
            "aliases": aliases,
            "source_dataset": "ddinter",
            "created_at": now,
            "updated_at": now
        }
        documents.append(doc)
        
    print(f"Bulk inserting {len(documents)} drugs into 'drug_master'...")
    
    # Insert in chunks of 5000
    chunk_size = 5000
    for i in range(0, len(documents), chunk_size):
        chunk = documents[i:i + chunk_size]
        master_col.insert_many(chunk)
        print(f"Inserted chunk {i // chunk_size + 1}/{(len(documents) - 1) // chunk_size + 1}")
        
    print("Rebuilding indexes for 'drug_master' collection...")
    master_col.create_index([("normalized_name", ASCENDING)], unique=True, name="normalized_name_unique")
    master_col.create_index([("aliases", ASCENDING)], name="aliases_index")
    
    print("drug_master seeding and indexing completed successfully!")
    client.close()

if __name__ == "__main__":
    seed_drug_master()
