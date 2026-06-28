import os
import sys
import time
from datetime import datetime, timezone
from pymongo import MongoClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.app.core.config import settings
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
    from app.core.config import settings

def run_validation():
    """Validates the imported drug interaction records in MongoDB."""
    print("Initializing validation engine...")
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    collection = db["drug_interactions"]
    
    report_lines = []
    report_lines.append("# Drug Interaction Database Import Validation Report")
    report_lines.append(f"Generated at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    report_lines.append("")
    
    print("Checking collection stats...")
    total_records = collection.count_documents({})
    print(f"Total records in 'drug_interactions': {total_records}")
    report_lines.append(f"## 1. Database Statistics")
    report_lines.append(f"- **Total Interaction Documents**: {total_records}")
    
    # 1. Malformed Rows Check
    print("Checking for malformed rows...")
    missing_fields = collection.count_documents({
        "$or": [
            {"drug_a": {"$exists": False}},
            {"drug_a_normalized": {"$exists": False}},
            {"drug_b": {"$exists": False}},
            {"drug_b_normalized": {"$exists": False}},
            {"severity": {"$exists": False}},
            {"interaction_id": {"$exists": False}}
        ]
    })
    empty_strings = collection.count_documents({
        "$or": [
            {"drug_a_normalized": ""},
            {"drug_b_normalized": ""},
            {"severity": ""}
        ]
    })
    malformed_total = missing_fields + empty_strings
    print(f"Malformed records found: {malformed_total}")
    report_lines.append(f"- **Malformed/Incomplete Documents**: {malformed_total}")
    
    # 2. Duplicate Detection
    print("Checking for duplicates...")
    pipeline = [
        {"$group": {"_id": {"a": "$drug_a_normalized", "b": "$drug_b_normalized"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}},
        {"$count": "duplicate_pairs"}
    ]
    agg_res = list(collection.aggregate(pipeline))
    duplicate_count = agg_res[0]["duplicate_pairs"] if agg_res else 0
    print(f"Duplicate pairs found: {duplicate_count}")
    report_lines.append(f"- **Duplicate Pairs**: {duplicate_count}")
    
    # 3. Bidirectional Record Verification
    print("Verifying bidirectional constraints...")
    # Fetch 100 samples
    sample_records = list(collection.find().limit(100))
    bidirectional_failures = 0
    for sample in sample_records:
        rev_a = sample["drug_b_normalized"]
        rev_b = sample["drug_a_normalized"]
        # Find reverse match
        reverse = collection.find_one({"drug_a_normalized": rev_a, "drug_b_normalized": rev_b})
        if not reverse:
            bidirectional_failures += 1
            
    print(f"Bidirectional sample verification failures: {bidirectional_failures}/100")
    report_lines.append(f"- **Bidirectional Sample Integrity Failures**: {bidirectional_failures}/100")
    
    # 4. Severity Distribution
    print("Analyzing severity distribution...")
    severity_counts = {}
    for s in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]:
        severity_counts[s] = collection.count_documents({"severity": s})
    print(f"Severity distribution: {severity_counts}")
    report_lines.append("")
    report_lines.append("## 2. Severity Distribution")
    for s, c in severity_counts.items():
        report_lines.append(f"- **{s}**: {c}")
        
    # 5. Indexes Verification
    print("Verifying index health...")
    indexes = collection.index_information()
    index_names = list(indexes.keys())
    print(f"Active indexes: {index_names}")
    report_lines.append("")
    report_lines.append("## 3. Database Indexes")
    for idx_name, idx_info in indexes.items():
        report_lines.append(f"- **{idx_name}**: Keys: `{idx_info['key']}`, Unique: `{idx_info.get('unique', False)}`")
        
    # 6. Lookup Latency Benchmark
    print("Running performance benchmark...")
    test_queries = [
        ("naltrexone", "abacavir"),
        ("abacavir", "naltrexone"),
        ("aspirin", "warfarin"),
        ("warfarin", "aspirin"),
        ("dexamethasone", "dolutegravir"),
        ("dolutegravir", "dexamethasone"),
        ("clarithromycin", "fentanyl"),
        ("fentanyl", "clarithromycin")
    ]
    
    latencies = []
    successful_lookups = 0
    for da, db_name in test_queries:
        start_time = time.perf_counter()
        result = collection.find_one({"drug_a_normalized": da, "drug_b_normalized": db_name})
        latency = (time.perf_counter() - start_time) * 1000.0  # in ms
        latencies.append(latency)
        if result:
            successful_lookups += 1
            
    avg_latency = sum(latencies) / len(latencies)
    print(f"Average lookup latency: {avg_latency:.4f} ms")
    report_lines.append("")
    report_lines.append("## 4. Performance Benchmark (Lookup Latency)")
    report_lines.append(f"- **Test Queries Executed**: {len(test_queries)}")
    report_lines.append(f"- **Successful Lookups**: {successful_lookups}/{len(test_queries)}")
    report_lines.append(f"- **Average Lookup Latency**: `{avg_latency:.4f} ms`")
    
    # Validation Asserts
    is_valid = True
    validation_status = []
    
    if total_records == 0:
        is_valid = False
        validation_status.append("- ❌ FAIL: Collection is empty.")
    else:
        validation_status.append("-  PASS: Collection has records.")
        
    if malformed_total > 0:
        is_valid = False
        validation_status.append(f"- ❌ FAIL: Found {malformed_total} malformed/incomplete records.")
    else:
        validation_status.append("-  PASS: No malformed/incomplete records.")
        
    if duplicate_count > 0:
        is_valid = False
        validation_status.append(f"- ❌ FAIL: Found {duplicate_count} duplicate pairs.")
    else:
        validation_status.append("-  PASS: No duplicate pairs.")
        
    if bidirectional_failures > 0:
        is_valid = False
        validation_status.append(f"- ❌ FAIL: Found {bidirectional_failures}/100 bidirectional sample matching failures.")
    else:
        validation_status.append("-  PASS: Bidirectional sample matching verified successfully.")
        
    if "unique_bidirectional_idx" not in index_names:
        is_valid = False
        validation_status.append("- ❌ FAIL: Compound unique index `unique_bidirectional_idx` is missing.")
    else:
        validation_status.append("-  PASS: Compound unique index `unique_bidirectional_idx` is active.")
        
    # Set threshold based on local vs remote connection
    is_remote = "localhost" not in settings.MONGODB_URL and "127.0.0.1" not in settings.MONGODB_URL
    threshold = 150.0 if is_remote else 5.0
    
    if avg_latency > threshold:
        is_valid = False
        validation_status.append(f"- ❌ FAIL: Average lookup latency `{avg_latency:.2f}ms` is above {threshold}ms threshold.")
    else:
        validation_status.append(f"-  PASS: Average lookup latency `{avg_latency:.2f}ms` is within the <{threshold}ms threshold.")
        
    report_lines.append("")
    report_lines.append("## 5. Overall Validation Summary")
    for status in validation_status:
        report_lines.append(status)
    report_lines.append("")
    
    final_status = "SUCCESS" if is_valid else "FAILED"
    report_lines.append(f"**Overall Validation Status**: `{final_status}`")
    
    # Save Report
    report_content = "\n".join(report_lines)
    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ddinter", "import_summary.md")
    
    with open(report_path, "w", encoding="utf-8") as rf:
        rf.write(report_content)
        
    print(f"Validation report saved to: {report_path}")
    print(f"Overall validation status: {final_status}")
    
    client.close()
    
    if not is_valid:
        print("Validation errors occurred. Please check database import status.")
        sys.exit(1)

if __name__ == "__main__":
    run_validation()
