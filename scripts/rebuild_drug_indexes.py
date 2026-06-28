import os
import sys
from pymongo import MongoClient, ASCENDING

# Add project root to sys.path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.core.config import settings
except ImportError:
    # If app path is different, adjust path addition
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
    from app.core.config import settings

def rebuild_indexes():
    """Rebuilds indexes on the drug_interactions MongoDB collection."""
    print(f"Connecting to MongoDB at: {settings.MONGODB_URL}")
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    collection = db["drug_interactions"]
    
    print("Rebuilding indexes for 'drug_interactions' collection...")
    
    # 1. Unique compound index for fast, deduplicated A -> B lookups
    print("Creating compound unique index (drug_a_normalized, drug_b_normalized)...")
    collection.create_index(
        [("drug_a_normalized", ASCENDING), ("drug_b_normalized", ASCENDING)],
        unique=True,
        name="unique_bidirectional_idx"
    )
    
    # 2. Individual index on drug_a_normalized
    print("Creating index on drug_a_normalized...")
    collection.create_index([("drug_a_normalized", ASCENDING)], name="drug_a_norm_idx")
    
    # 3. Individual index on drug_b_normalized
    print("Creating index on drug_b_normalized...")
    collection.create_index([("drug_b_normalized", ASCENDING)], name="drug_b_norm_idx")
    
    # 4. Index on severity
    print("Creating index on severity...")
    collection.create_index([("severity", ASCENDING)], name="severity_idx")
    
    print("All indexes created successfully!")
    client.close()

if __name__ == "__main__":
    rebuild_indexes()
