# Nura - Application Flow Document

# 1. Overview

This document describes all major user journeys and workflows inside the Nura Healthcare Platform.

The purpose of this document is to provide a clear understanding of how users interact with the platform and how different services communicate during those interactions.

---

# 2. User Roles

| Role    | Description            |
| ------- | ---------------------- |
| Patient | Healthcare consumer    |
| Doctor  | Healthcare provider    |
| Admin   | Platform administrator |

---

# 3. Authentication Flow

## Registration Flow

```text
User
 ↓
Register
 ↓
Enter Details
 ↓
Email OTP Sent
 ↓
OTP Verification
 ↓
Account Created
 ↓
Dashboard
```

---

## Login Flow

```text
User
 ↓
Email + Password
 ↓
JWT Authentication
 ↓
Role Detection
 ↓
Dashboard
```

---

## Google Login Flow

```text
User
 ↓
Google OAuth
 ↓
Google Verification
 ↓
JWT Generation
 ↓
Dashboard
```

---

## Forgot Password Flow

```text
User
 ↓
Forgot Password
 ↓
Email OTP
 ↓
OTP Verification
 ↓
New Password
 ↓
Login
```

---

# 4. Patient Dashboard Flow

```text
Login
 ↓
Patient Dashboard
 ↓
Health Overview
 ↓
Quick Actions
```

Dashboard Displays:

* Reports
* Reminders
* Appointments
* Health Insights
* Risk Indicators

---

# 5. Nura AI Chat Flow

## High-Level Flow

```text
User Query
 ↓
Router Agent
 ↓
Retrieval Agent
 ↓
Context Retrieval
 ↓
Agent Selection
 ↓
Groq LLM
 ↓
Memory Update
 ↓
Response
```

---

## Context Retrieval Flow

```text
Query
 ↓
Generate Embedding
 ↓
Qdrant Search
 ↓
Retrieve Relevant Context
 ↓
Build Prompt
 ↓
Agent Execution
```

Sources:

* Reports
* Chat Memory
* Medical Knowledge
* Drug Knowledge
* Appointment History
* Prescriptions
* Consultations

---

## Chat Memory Flow

```text
User Message
 ↓
Agent Response
 ↓
Memory Agent
 ↓
Store in Qdrant
 ↓
Store Metadata in MongoDB
```

---

# 6. Symptom Analysis Flow

```text
User Symptoms
 ↓
Router Agent
 ↓
Symptom Analysis Agent
 ↓
Context Retrieval
 ↓
Groq Analysis
 ↓
Risk Categorization
 ↓
Guidance
```

Outputs:

* Risk Level
* Recommendations
* Doctor Specialty Suggestions

---

# 7. Medical Question Flow

```text
User Question
 ↓
Medical Knowledge Agent
 ↓
Knowledge Retrieval
 ↓
Groq Reasoning
 ↓
Response
```

---

# 8. Report Upload Flow

## Upload Flow

```text
Upload Report
 ↓
File Validation
 ↓
Storage Upload
 ↓
OCR Extraction
 ↓
Text Processing
 ↓
Chunking
 ↓
Embedding Generation
 ↓
Qdrant Storage
```

---

## Analysis Flow

```text
Report Text
 ↓
Report Analysis Agent
 ↓
Medical Entity Extraction
 ↓
Summary Generation
 ↓
Risk Classification
 ↓
Dashboard Update
```

Outputs:

* Summary
* Insights
* Risk Level
* Recommendations

---

# 9. Historical Report Comparison Flow

```text
New Report
 ↓
Retrieve Previous Reports
 ↓
Trend Analysis
 ↓
Health Progress Evaluation
 ↓
Insight Generation
```

Example:

* Cholesterol Trend
* Blood Sugar Trend
* Blood Pressure Trend

---

# 10. Drug Interaction Flow

## Chat-Based Check

```text
User Query
 ↓
Drug Interaction Agent
 ↓
RxNorm Normalization
 ↓
Drug Dataset Lookup
 ↓
Interaction Detection
 ↓
Risk Classification
 ↓
Recommendation
```

---

## Reminder-Based Check

```text
Create Medication Reminder
 ↓
Drug Interaction Agent
 ↓
Medication Validation
 ↓
Risk Classification
 ↓
User Confirmation
 ↓
Reminder Creation
```

---

## Risk Classification

### Low Risk

```text
Display Information
 ↓
Create Reminder
```

### Medium Risk

```text
Display Warning
 ↓
User Confirmation
 ↓
Create Reminder
```

### High Risk

```text
Display Strong Warning
 ↓
User Confirmation Required
 ↓
Reminder Creation
```

---

# 11. Doctor Discovery Flow

```text
Search Doctor
 ↓
Apply Filters
 ↓
Retrieve Doctors
 ↓
AI Ranking
 ↓
Recommendations
 ↓
Doctor Profile
```

Filters:

* Specialty
* Experience
* Fee
* Availability

---

# 12. Appointment Booking Flow

## Appointment Creation

```text
Search Doctor
 ↓
Select Doctor
 ↓
Select Slot
 ↓
Payment
 ↓
Appointment Request
```

---

## Payment Flow

```text
Create Razorpay Order
 ↓
Payment Gateway
 ↓
Payment Success
 ↓
Verification
 ↓
Appointment Created
```

---

## Approval Flow

```text
Appointment Request
 ↓
Doctor Review
 ↓
Approve / Reject
```

### If Approved

```text
Appointment Confirmed
 ↓
Notification Sent
```

### If Rejected

```text
Appointment Cancelled
 ↓
Refund Initiated
```

---

# 13. Consultation Flow

```text
Confirmed Appointment
 ↓
Doctor Opens Patient Context
 ↓
AI Summary Generated
 ↓
Consultation
 ↓
Doctor Notes
 ↓
Prescription Upload
 ↓
Follow-Up Recommendation
 ↓
Consultation Complete
```

---

# 14. AI Patient Context Flow

Before consultation:

```text
Appointment
 ↓
Retrieve Reports
 ↓
Retrieve Medications
 ↓
Retrieve Appointments
 ↓
Retrieve Consultations
 ↓
Generate Summary
 ↓
Doctor Dashboard
```

Doctor Receives:

* Health Summary
* Recent Reports
* Active Medications
* Recent Appointments
* Drug Alerts

---

# 15. Prescription Flow

```text
Doctor Uploads Prescription
 ↓
Store in MongoDB
 ↓
Patient Notification
 ↓
Prescription History Update
```

---

# 16. Reminder Flow

```text
Add Reminder
 ↓
Validation
 ↓
Schedule Reminder
 ↓
Notification Generation
 ↓
Reminder Active
```

Reminder Types:

* Medication
* Appointment
* Follow-Up

---

# 17. Notification Flow

Triggers:

* Appointment Approved
* Appointment Rejected
* Reminder Due
* Report Analysis Complete
* Prescription Uploaded

Flow:

```text
Event Trigger
 ↓
Notification Service
 ↓
Store Notification
 ↓
User Delivery
```

---

# 18. Doctor Earnings Flow

```text
Payment Success
 ↓
Revenue Split
 ↓
Doctor Share
 ↓
Wallet Update
```

Example:

```text
₹500 Consultation

Doctor: ₹425
Platform: ₹75
```

---

# 19. Admin Flow

## Doctor Verification

```text
Doctor Registration
 ↓
Document Review
 ↓
Approve / Reject
```

---

## User Management

```text
View Users
 ↓
Manage Accounts
 ↓
Activate / Deactivate
```

---

# 20. End-to-End Platform Flow

```text
User Registration
 ↓
Dashboard
 ↓
Reports
 ↓
AI Analysis
 ↓
Chat with Nura
 ↓
Doctor Discovery
 ↓
Appointment Booking
 ↓
Payment
 ↓
Consultation
 ↓
Prescription
 ↓
Reminder Creation
 ↓
Ongoing Healthcare Support
```

---

# 21. Future Flows

Future planned workflows:

* Voice Assistant
* Telemedicine Video Calls
* Wearable Device Integration
* Insurance Claims
* Predictive Health Monitoring
* Emergency Assistance
