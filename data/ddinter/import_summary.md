# Drug Interaction Database Import Validation Report
Generated at: 2026-06-28 09:32:03 UTC

## 1. Database Statistics
- **Total Interaction Documents**: 300840
- **Malformed/Incomplete Documents**: 0
- **Duplicate Pairs**: 0
- **Bidirectional Sample Integrity Failures**: 0/100

## 2. Severity Distribution
- **LOW**: 12318
- **MEDIUM**: 178132
- **HIGH**: 50764
- **UNKNOWN**: 59626

## 3. Database Indexes
- **_id_**: Keys: `[('_id', 1)]`, Unique: `False`
- **unique_bidirectional_idx**: Keys: `[('drug_a_normalized', 1), ('drug_b_normalized', 1)]`, Unique: `True`
- **drug_a_norm_idx**: Keys: `[('drug_a_normalized', 1)]`, Unique: `False`
- **drug_b_norm_idx**: Keys: `[('drug_b_normalized', 1)]`, Unique: `False`
- **severity_idx**: Keys: `[('severity', 1)]`, Unique: `False`

## 4. Performance Benchmark (Lookup Latency)
- **Test Queries Executed**: 8
- **Successful Lookups**: 6/8
- **Average Lookup Latency**: `74.8690 ms`

## 5. Overall Validation Summary
-  PASS: Collection has records.
-  PASS: No malformed/incomplete records.
-  PASS: No duplicate pairs.
-  PASS: Bidirectional sample matching verified successfully.
-  PASS: Compound unique index `unique_bidirectional_idx` is active.
-  PASS: Average lookup latency `74.87ms` is within the <150.0ms threshold.

**Overall Validation Status**: `SUCCESS`