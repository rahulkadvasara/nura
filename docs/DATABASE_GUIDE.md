# Nura - Database Guide

## 1. Purpose

This document defines the database architecture of Nura.

It serves as the source of truth for:

* MongoDB collections
* Qdrant collections
* Relationships
* Indexing strategy
* Data lifecycle
* Storage responsibilities

---

# 2. Database Architecture

Nura uses two databases.

## MongoDB Atlas

Stores:

```text
Application Data
User Data
Appointments
Payments
Reports Metadata
Notifications
Agent Logs
```

---

## Qdrant

Stores:

```text
patient_reports
medical_knowledge
drug_knowledge
chat_memory
doctor_knowledge
```

---

# 3. MongoDB Collections

## users

Stores platform users.

```json
{
  "_id": "ObjectId",
  "role": "patient|doctor|admin",
  "email": "string",
  "password_hash": "string",
  "full_name": "string",
  "phone": "string",
  "profile_picture": "string",
  "auth_provider": "local|google",
  "email_verified": true,
  "is_active": true,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## refresh_tokens

Stores active refresh tokens.

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "token_hash": "string",
  "expires_at": "datetime",
  "revoked": false,
  "created_at": "datetime"
}
```

---

## doctor_profiles

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "specialization": "string",
  "experience_years": 5,
  "hospital": "string",
  "license_number": "string",
  "bio": "string",
  "consultation_fee": 500,
  "verification_status": "pending"
}
```

---

## doctor_documents

Doctor verification documents.

```json
{
  "_id": "ObjectId",
  "doctor_id": "ObjectId",
  "document_type": "license",
  "file_url": "string",
  "verification_status": "pending",
  "uploaded_at": "datetime",
  "verified_at": "datetime",
  "verified_by": "ObjectId"
}
```

---

## doctor_availability

```json
{
  "_id": "ObjectId",
  "doctor_id": "ObjectId",
  "available_date": "date",
  "start_time": "09:00",
  "end_time": "09:30",
  "is_booked": false
}
```

---

## appointments

```json
{
  "_id": "ObjectId",
  "patient_id": "ObjectId",
  "doctor_id": "ObjectId",
  "availability_id": "ObjectId",
  "status": "pending",
  "appointment_date": "datetime",
  "reason": "string"
}
```

### Statuses

```text
pending
approved
rejected
completed
cancelled
```

---

## payments

```json
{
  "_id": "ObjectId",
  "appointment_id": "ObjectId",
  "patient_id": "ObjectId",
  "doctor_id": "ObjectId",
  "amount": 500,
  "platform_fee": 75,
  "doctor_share": 425,
  "payment_status": "held",
  "transaction_id": "string"
}
```

### Payment States

```text
pending
held
approved
completed
refunded
failed
```

---

## consultations

```json
{
  "_id": "ObjectId",
  "appointment_id": "ObjectId",
  "patient_id": "ObjectId",
  "doctor_id": "ObjectId",
  "diagnosis": "string",
  "doctor_notes": "string",
  "follow_up_date": "datetime"
}
```

---

## prescriptions

```json
{
  "_id": "ObjectId",
  "consultation_id": "ObjectId",
  "file_url": "string",
  "notes": "string"
}
```

---

## reports

```json
{
  "_id": "ObjectId",
  "patient_id": "ObjectId",
  "file_url": "string",
  "raw_text": "string",
  "structured_data": {},
  "entities": [],
  "ai_summary": "string",
  "risk_level": "medium",
  "created_at": "datetime"
}
```

---

## patient_memory

AI-generated longitudinal patient summary. Continuously updated on important events.

```json
{
  "_id": "ObjectId",
  "patient_id": "ObjectId",
  "ai_summary": "string",
  "chronic_conditions": [],
  "allergies": [],
  "medications": [],
  "surgeries": [],
  "diagnoses": [],
  "health_risks": [],
  "recent_findings": [],
  "lifestyle_notes": "string",
  "timeline": [],
  "last_updated": "datetime"
}
```

---

## health_insights

AI-generated insights.

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "description": "string",
  "severity": "medium",
  "source_report_id": "ObjectId",
  "created_at": "datetime"
}
```

---

## reminders

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "description": "string",
  "reminder_time": "08:00",
  "repeat_type": "daily",
  "is_active": true
}
```

---

## notifications

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "message": "string",
  "type": "appointment",
  "is_read": false,
  "created_at": "datetime"
}
```

---

## notification_preferences

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "email_enabled": true,
  "appointment_enabled": true,
  "reminder_enabled": true,
  "report_enabled": true,
  "marketing_enabled": false
}
```

---

## chat_sessions

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "Health Discussion"
}
```

---

## chat_messages

```json
{
  "_id": "ObjectId",
  "session_id": "ObjectId",
  "role": "user",
  "content": "message"
}
```

---

## doctor_wallets

```json
{
  "_id": "ObjectId",
  "doctor_id": "ObjectId",
  "balance": 2500
}
```

---

## agent_logs

```json
{
  "_id": "ObjectId",
  "agent_name": "ReportAnalysisAgent",
  "user_id": "ObjectId",
  "query": "message",
  "latency_ms": 2400,
  "status": "success",
  "created_at": "datetime"
}
```

---

## audit_logs

```json
{
  "_id": "ObjectId",
  "actor_id": "ObjectId",
  "actor_role": "admin",
  "action": "doctor_approved",
  "resource_type": "doctor",
  "resource_id": "ObjectId",
  "timestamp": "datetime"
}
```

---

# 4. Qdrant Collections

## patient_reports

Stores:

```text
Report Chunks
Report Embeddings
```

---

## chat_memory

Stores:

```text
Long-Term Memory
Conversation Embeddings
```

---

## medical_knowledge

Stores:

```text
Medical Articles
Healthcare Guidelines
Educational Content
```

---

## drug_knowledge

Stores:

```text
Drug Safety Data
Drug Interaction Knowledge
RxNorm Related Data
```

---

## doctor_knowledge

Stores:

```text
Doctor Metadata
Specialization Knowledge
Doctor Recommendation Data
```

---

# 5. Relationship Overview

```text
User
│
├── Doctor Profile
│   ├── Doctor Documents
│   ├── Availability
│   └── Wallet
│
├── Reports
│   └── Health Insights
│
├── Reminders
│
├── Appointments
│   ├── Consultations
│   └── Payments
│
└── Chat Sessions
    └── Chat Messages
```

---

# 6. MongoDB Indexing Strategy

## users

```text
email (unique)
role
```

---

## appointments

```text
patient_id
doctor_id
appointment_date
status
```

---

## reports

```text
patient_id
created_at
risk_level
```

---

## reminders

```text
user_id
reminder_time
```

---

## payments

```text
appointment_id
doctor_id
payment_status
```

---

## health_insights

```text
user_id
severity
created_at
```

---

# 7. Data Retention

## Reports

Retain indefinitely.

---

## Appointments

Retain indefinitely.

---

## Chat Messages

Retain indefinitely unless deleted by user.

---

## Agent Logs

Retain:

```text
90 Days
```

---

## Audit Logs

Retain:

```text
1 Year
```

---

# 8. Source of Truth

| Data Type         | Source  |
| ----------------- | ------- |
| User Data         | MongoDB |
| Operational Data  | MongoDB |
| Reports Metadata  | MongoDB |
| Report Embeddings | Qdrant  |
| Chat History      | MongoDB |
| Chat Memory       | Qdrant  |
| Medical Knowledge | Qdrant  |
| Drug Knowledge    | Qdrant  |
| Doctor Profiles   | MongoDB |
| Doctor Knowledge  | Qdrant  |
| Patient Context   | MongoDB (patient_memory) |
| Appointments      | MongoDB |
| Payments          | MongoDB |

---

# 9. Definition of Done

Database architecture is considered complete when:

* All collections exist
* Indexes are created
* Relationships are validated
* Qdrant collections are provisioned
* Data ownership is clearly defined
* Retention policies are documented

```
```
