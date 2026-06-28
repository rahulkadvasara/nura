# Nura - Technical Requirements Document (TRD)

## 1. System Overview

Nura is a Retrieval-Augmented Multi-Agent Healthcare Platform built using:

* Next.js (Frontend)
* FastAPI (Backend)
* MongoDB Atlas (Primary Database)
* Qdrant (Vector Database)
* Groq Cloud (LLM)
* LangGraph (Agent Orchestration)
* Razorpay (Payments)

---

# 2. High-Level Architecture

```text
Patient/Doctor/Admin
        │
        ▼
     Frontend
    (Next.js)
        │
        ▼
     FastAPI
        │
 ┌──────┼──────┐
 ▼      ▼      ▼

MongoDB Qdrant Groq

        │
        ▼

   LangGraph
 Multi-Agent Layer
```

---

# 3. Technology Stack

| Layer            | Technology         |
| ---------------- | ------------------ |
| Frontend         | Next.js 15         |
| Language         | TypeScript         |
| Styling          | Tailwind CSS       |
| UI Components    | shadcn/ui          |
| State Management | Zustand            |
| Data Fetching    | TanStack Query     |
| Backend          | FastAPI            |
| Validation       | Pydantic           |
| Authentication   | JWT + Google OAuth |
| Database         | MongoDB Atlas      |
| Vector Database  | Qdrant             |
| Agent Framework  | LangGraph          |
| LLM              | Groq               |
| Payment Gateway  | Razorpay           |
| Storage          | Supabase Storage   |
| Deployment FE    | Vercel             |
| Deployment BE    | Railway / Render   |

---

# 4. User Roles

| Role    | Description            |
| ------- | ---------------------- |
| Patient | Healthcare consumer    |
| Doctor  | Healthcare provider    |
| Admin   | Platform administrator |

---

# 5. Authentication Architecture

Supported Authentication:

1. Email + Password
2. Google OAuth
3. Forgot Password via OTP

Authentication Flow:

```text
Register
 ↓
Email OTP
 ↓
Verification
 ↓
Login
 ↓
JWT Access Token
 ↓
Protected Routes
```

---

# 6. AI Architecture

Nura uses a Multi-Agent Architecture.

## Agents

| Agent                       | Responsibility        |
| --------------------------- | --------------------- |
| Router Agent                | Intent Classification |
| Retrieval Agent             | Context Retrieval     |
| Symptom Agent               | Symptom Analysis      |
| Medical Knowledge Agent     | Healthcare Q&A        |
| Report Analysis Agent       | Report Understanding  |
| Drug Interaction Agent      | Medication Safety     |
| Doctor Recommendation Agent | Doctor Discovery      |
| Reminder Agent              | Reminder Management   |
| Appointment Agent           | Appointment Workflow  |
| Memory Agent                | Long-Term Memory      |


## Patient Context Builder

Responsibilities:

- Aggregate reports
- Aggregate prescriptions
- Aggregate appointments
- Aggregate reminders
- Build unified patient context

The context builder runs after retrieval and before specialized agent execution.

---

# 7. LangGraph Workflow

```text
User Query (via Phase 12.5 Chat Interface)
 ↓
Intent Detection
 ↓
Retrieval Agent
 ↓
Context Aggregation
 ↓
Agent Routing
 ↓
Specialized Agent
 ↓
Groq LLM
 ↓
Memory Agent
 ↓
Response (streamed to Chat Interface)
```

*Note: The Chat Interface layer (Phase 12.5 Conversational AI Platform) manages session persistence, streaming, and conversation history, serving as the user-facing layer for this AI architecture.*

---

# 8. Retrieval-Augmented Generation (RAG)

## Retrieval Sources

### Qdrant

* patient_reports
* medical_knowledge
* chat_memory
* doctor_knowledge

### MongoDB

* User Metadata
* drug_master
* drug_interactions
* Appointments
* Consultations
* Prescriptions
* Reminders
* Doctor Availability

---

## RAG Workflow

```text
User Query
 ↓
Intent Detection
 ↓
Patient Context Builder
 ↓
Embedding
 ↓
Multi-Collection Retrieval
 ↓
Context Ranking
 ↓
Prompt Construction
 ↓
Groq LLM
 ↓
Response
```

---

# 9. Drug Interaction Workflow

```text
Medicine Input
 ↓
Normalize Drug (drug_master)
 ↓
Collect Patient Medications
 ↓
Determine Severity (drug_interactions)
 ↓
Generate Explanation (Groq)
 ↓
Response
```

Risk Levels:

| Level  | Meaning                    |
| ------ | -------------------------- |
| LOW    | Informational              |
| MEDIUM | User Confirmation Required |
| HIGH   | Strong Warning             |
| UNKNOWN| Review Required            |

---

# 10. Reminder Safety Workflow

```text
Add Medication Reminder
 ↓
Normalize Medicine Name
 ↓
Collect Current Patient Medications
 ↓
Determine Severity (drug_interactions)
 ↓
Allow, Warning, or Block
 ↓
Reminder Stored
```

---

# 11. Appointment Workflow

```text
Search Doctor
 ↓
Select Slot
 ↓
Payment
 ↓
Appointment Request
 ↓
Doctor Approval
 ↓
Consultation
 ↓
Prescription
 ↓
Follow-Up
```

---

# 12. Report Analysis Workflow

```text
Upload Report
 ↓
OCR Extraction
 ↓
Chunking
 ↓
Embedding Generation
 ↓
Qdrant Storage
 ↓
Report Analysis Agent
 ↓
AI Summary
 ↓
Dashboard Display
```


```
OCR
↓
Structured Extraction
↓
Medical Entity Extraction
↓
Risk Detection
↓
Groq Summary
```

---

# 13. Payment Workflow

```text
Patient Payment
 ↓
Razorpay
 ↓
Payment Verification
 ↓
Appointment Confirmation
 ↓
Revenue Split
```

```
Payment
↓
Escrow Hold
↓
Appointment Request
↓
Doctor Approval
```


Revenue Distribution:

| Receiver | Share |
| -------- | ----- |
| Doctor   | 85%   |
| Platform | 15%   |

---

# 14. Vector Database Design

Qdrant Collections:

| Collection        |
| ----------------- |
| patient_reports   |
| medical_knowledge |
| chat_memory       |
| doctor_knowledge  |

---

# 15. AI Responsibilities

| Component | Responsibilities |
| --------- | ---------------- |
| MongoDB   | Transactional data, operational records, patient_memory |
| Qdrant    | Semantic retrieval, embeddings, similarity search |
| Groq      | Reasoning, summarization, response generation |
| LangGraph | Orchestration, routing, workflows |

---

# 16. Doctor Dashboard Pattern

Doctor dashboards should never invoke the LLM dynamically.

```text
Doctor opens patient
 ↓
Read patient_memory (MongoDB)
 ↓
Display summary
 ↓
Fetch supporting MongoDB records
```
This provides low latency and predictable behavior.

---

# 15. API Architecture

```text
/api/v1

/auth
/users
/doctors
/appointments
/payments
/reports
/reminders
/chat
/admin
```

---

# 16. Security Requirements

Authentication:

* JWT
* Refresh Tokens
* Google OAuth

Authorization:

* RBAC
* Route Guards

Data Security:

* Password Hashing
* HTTPS
* Environment Secrets

---

# 17. Performance Targets

| Metric         | Target  |
| -------------- | ------- |
| API Response   | < 500ms |
| Chat Response  | < 5s    |
| Vector Search  | < 1s    |
| Authentication | < 300ms |

---

# 18. Deployment Architecture

Frontend:

* Vercel

Backend:

* Railway or Render

Services:

* MongoDB Atlas
* Qdrant Cloud
* Groq Cloud
* Razorpay
* Supabase Storage

---

# 19. Monitoring

Application Monitoring:

* Backend Logs
* Agent Logs
* Payment Logs
* Error Tracking

Metrics:

* Chat Usage
* Report Uploads
* Appointment Bookings
* Reminder Usage

---

# 21. Future Enhancements

* Voice Assistant
* Wearable Integration
* Telemedicine Calls
* Insurance Integration
* Mobile Apps
* Predictive Health Analytics

---

# 22. Future Agent Compatibility

This architecture is designed to natively support new agents without requiring architectural changes:

* Symptom Agent
* Report Analysis Agent
* Drug Interaction Agent
* Doctor Recommendation Agent
* Reminder Agent
* Appointment Agent
* Memory Agent
