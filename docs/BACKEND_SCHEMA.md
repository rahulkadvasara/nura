# Nura - Backend Schema Document

# 1. Backend Overview

Nura Backend is built using:

* FastAPI
* MongoDB Atlas
* Qdrant
* LangGraph
* Groq
* Razorpay

Architecture Style:

* Modular Monolith
* Service Layer Pattern
* Repository Pattern
* Domain-Based Structure

---

# 2. Backend Folder Structure

```text
backend/

├── app/
│
├── api/
│   └── v1/
│       ├── auth/
│       ├── users/
│       ├── doctors/
│       ├── appointments/
│       ├── payments/
│       ├── reports/
│       ├── reminders/
│       ├── chat/
│       ├── notifications/
│       └── admin/
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── dependencies.py
│   ├── database.py
│   └── qdrant.py
│
├── models/
│   ├── user.py
│   ├── doctor.py
│   ├── appointment.py
│   ├── payment.py
│   ├── report.py
│   ├── reminder.py
│   ├── notification.py
│   └── chat.py
│
├── schemas/
│   ├── auth.py
│   ├── user.py
│   ├── doctor.py
│   ├── appointment.py
│   ├── payment.py
│   ├── report.py
│   ├── reminder.py
│   └── chat.py
│
├── repositories/
│   ├── user_repository.py
│   ├── doctor_repository.py
│   ├── appointment_repository.py
│   ├── payment_repository.py
│   ├── report_repository.py
│   ├── reminder_repository.py
│   └── chat_repository.py
│
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── doctor_service.py
│   ├── appointment_service.py
│   ├── payment_service.py
│   ├── report_service.py
│   ├── reminder_service.py
│   ├── notification_service.py
│   └── chat_service.py
│
├── ai/
│   ├── agents/
│   ├── graph/
│   ├── retrieval/
│   ├── memory/
│   ├── prompts/
│   └── tools/
│
├── middleware/
│
├── utils/
│
├── tests/
│
└── main.py
```

---

# 3. MongoDB Collections

## users

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
  "reason": "string",
  "meeting_link": "string"
}
```

Statuses:

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
  "payment_status": "paid",
  "transaction_id": "string"
}
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
  "risk_level": "medium"
}
```

---

## patient_memory

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
  "is_read": false
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

## drug_interactions

```json
{
  "_id": "ObjectId",
  "drug_a": "aspirin",
  "drug_b": "warfarin",
  "severity": "high",
  "description": "Increased bleeding risk",
  "source": "rxnorm"
}
```
---

## drug_master

```json
{
  "_id": "ObjectId",
  "generic_name": "string",
  "brand_names": ["string"],
  "aliases": ["string"],
  "drug_class": "string",
  "dosage_forms": ["string"],
  "strengths": ["string"],
  "manufacturer": "string",
  "rxnorm_code": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
---

## refresh_tokens

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

## doctor_documents

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

## health_insights

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "type": "report",
  "title": "Elevated Cholesterol",
  "description": "Cholesterol levels increased compared to previous report",
  "severity": "medium",
  "source_report_id": "ObjectId",
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

## agent_logs

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "agent_name": "symptom_agent",
  "query": "I have fever",
  "response": "Possible viral infection",
  "execution_time_ms": 1250,
  "created_at": "datetime"
}
```

---

## audit_logs

```json
{
  "_id": "ObjectId",
  "admin_id": "ObjectId",
  "action": "string",
  "target_id": "ObjectId",
  "target_type": "string",
  "details": {},
  "ip_address": "string",
  "user_agent": "string",
  "created_at": "datetime"
}
```

---

# 4. Qdrant Collections

## patient_reports

Stores:

* Report embeddings
* Report chunks

---

## chat_memory

Stores:

* Chat embeddings
* Long-term memory

---

## medical_knowledge

Stores:

* Medical knowledge chunks
* Educational data

---



## doctor_knowledge

Stores:

* Doctor metadata
* Specialization knowledge
* Doctor recommendation data

---




# 5. API Structure

Base URL:

```text
/api/v1
```

---

## Auth APIs

```text
POST   /auth/register
POST   /auth/verify-otp
POST   /auth/login
POST   /auth/google
POST   /auth/forgot-password
POST   /auth/reset-password
GET    /auth/me
```

---

## User APIs

```text
GET    /users/profile
PUT    /users/profile
GET    /users/dashboard
```

---

## Doctor APIs

```text
GET    /doctors
GET    /doctors/{id}
POST   /doctors/availability
PUT    /doctors/availability/{id}
DELETE /doctors/availability/{id}
```

---

## Appointment APIs

```text
POST   /appointments
GET    /appointments
GET    /appointments/{id}
PUT    /appointments/{id}
POST   /appointments/{id}/approve
POST   /appointments/{id}/reject
```

---

## Payment APIs

```text
POST   /payments/create-order
POST   /payments/verify
GET    /payments/history
```

---

## Report APIs

```text
POST   /reports/upload
GET    /reports
GET    /reports/{id}
DELETE /reports/{id}
```

---

## Reminder APIs

```text
POST   /reminders
GET    /reminders
PUT    /reminders/{id}
DELETE /reminders/{id}
```

---

## Chat APIs

```text
POST   /chat/message
GET    /chat/sessions
GET    /chat/session/{id}
```

---

## Admin APIs

```text
POST   /admin/accounts
GET    /admin/accounts
GET    /admin/accounts/{id}
POST   /admin/accounts/{id}/disable
POST   /admin/accounts/{id}/enable
GET    /admin/users
GET    /admin/users/{id}
POST   /admin/users/{id}/suspend
POST   /admin/users/{id}/activate
GET    /admin/doctors
POST   /admin/doctors/{id}/approve
POST   /admin/doctors/{id}/reject
POST   /admin/doctors/{id}/suspend
POST   /admin/doctors/{id}/reactivate
GET    /admin/analytics
GET    /admin/audit-logs
```

---

# 6. Service Layer Responsibilities

| Service             | Responsibility      |
| ------------------- | ------------------- |
| AuthService         | Authentication      |
| UserService         | User Operations     |
| DoctorService       | Doctor Operations   |
| AppointmentService  | Appointment Logic   |
| PaymentService      | Razorpay Logic      |
| ReportService       | Report Processing   |
| ReminderService     | Reminder Processing |
| ChatService         | AI Chat             |
| NotificationService | Notifications       |
| AdminService        | Platform Operations |

---

# 7. AI Layer Structure

```text
ai/

agents/
graph/
retrieval/
memory/
prompts/
tools/
```

---

# 8. Agent Definitions

## Router Agent

Responsibilities:

* Intent Detection
* Agent Selection

---

## Retrieval Agent

Responsibilities:

* Query Embedding
* Vector Search
* Context Aggregation

---

## Symptom Agent

Responsibilities:

* Symptom Assessment
* Health Guidance

---

## Medical Knowledge Agent

Responsibilities:

* Medical Q&A

---

## Report Analysis Agent

Responsibilities:

* Report Understanding
* Report Summarization

---

## Drug Interaction Agent

Responsibilities:

* drug_master Normalization
* drug_interactions Lookup
* Deterministic Risk Classification

---

## Doctor Recommendation Agent

Responsibilities:

* Specialty Matching
* Doctor Ranking

---

## Reminder Agent

Responsibilities:

* Reminder Validation
* Reminder Creation

---

## Appointment Agent

Responsibilities:

* Appointment Logic
* Consultation Lifecycle

---

## Memory Agent

Responsibilities:

* Long-Term Memory
* Context Persistence

---

# 9. LangGraph State

```python
{
    "user_id": str,
    "query": str,
    "intent": str,
    "retrieved_context": list,
    "selected_agent": str,
    "response": str
}
```

---

# 10. Indexing Strategy

MongoDB:

Indexes:

* email
* role
* doctor_id
* patient_id
* appointment_date

Qdrant:

Indexes:

* report embeddings
* chat embeddings
* medical embeddings

---

# 11. Security Layer

Authentication:

* JWT
* Refresh Tokens
* Google OAuth

Authorization:

* Role-Based Access Control

Encryption:

* Password Hashing
* HTTPS

---

# 12. Future Backend Extensions

* Telemedicine
* Video Calls
* Insurance Claims
* Voice Assistant
* Wearable Devices
* Health Forecasting
