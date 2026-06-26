# Nura - Implementation Plan

# 1. Purpose

This document defines the development roadmap for Nura.

The goal is to build the platform incrementally while maintaining a production-ready architecture.

Each phase should result in a stable and testable system.

---

# 2. Current Progress

Phase 0: Completed
Phase 1: Completed
Phase 2: Completed
Phase 3: Completed
Phase 4: Completed
Phase 5: Completed
Phase 6: Completed
Phase 6.5: Completed
Phase 7: Completed
Phase 8: Completed
Current Focus: Phase 9 - Retrieval-Augmented Generation (Sprint 1: Document Indexing Pipeline Completed, Sprint 2: Retrieval Engine Completed)

---

# 3. Development Strategy

Development Order:

```text
Foundation
 ↓
Authentication
 ↓
Core CRUD Features
 ↓
Appointments
 ↓
Administration & Platform Operations
 ↓
Payments
 ↓
AI Infrastructure
 ↓
RAG
 ↓
Multi-Agent System
 ↓
Report Analysis
 ↓
Drug Safety
 ↓
Production Deployment
```

---

# 4. Milestone Overview

| Phase    | Name                                      | Duration |
| -------- | ----------------------------------------- | -------- |
| Phase 0  | Project Setup                             | Completed|
| Phase 1  | Authentication                            | Completed|
| Phase 2  | Frontend Authentication & User Experience | 2-3 Days |
| Phase 3  | Core Healthcare Data Layer                | 2-3 Days |
| Phase 4  | Dashboard System                          | 1-2 Days |
| Phase 5  | Doctor Management System                  | 2 Days   |
| Phase 6  | Appointment Management                    | 2 Days   |
| Phase 6.5| Administration & Platform Operations      | 3 Days   |
| Phase 7  | Payment System                            | 1 Day    |
| Phase 8  | AI Infrastructure                         | 2 Days   |
| Phase 9  | Retrieval-Augmented Generation            | 2 Days   |
| Phase 10 | Multi-Agent System                        | 3 Days   |
| Phase 11 | Report Analysis                           | 2 Days   |
| Phase 12 | Drug Safety                               | 2 Days   |
| Phase 13 | Testing & Deployment                      | 2 Days   |

Estimated MVP:

```text
25 - 30 Days
```

---

# PHASE 0: COMPLETE

Completed:

* Frontend foundation
* Backend foundation
* MongoDB Atlas connection
* Qdrant Cloud connection
* Environment management
* Health endpoint

---

# PHASE 1: COMPLETE

Completed:

Authentication System

Implemented:

* Registration
* OTP Verification
* Login
* JWT Authentication
* Refresh Tokens
* Logout
* Current User Endpoint
* Password Recovery
* Password Reset
* Google OAuth
* RBAC Foundation
* Authentication Dependencies
* Automated Tests

Authentication backend is considered production-ready for MVP.

---

# PHASE 2

# Frontend Authentication & User Experience

## Objective

Connect frontend to completed authentication backend.

---

## Features

Sprint 1:

* Axios Client
* React Query Integration
* Zustand Auth Store
* Token Persistence
* Protected Routes
* Role Guards

Sprint 2:

* Login Page
* Register Page
* OTP Verification Page
* Forgot Password Page
* Reset Password Page

Sprint 3:

* Google Sign-In UI
* Session Initialization
* Logout Flow

Sprint 4:

* Profile Page
* Account Settings
* Notification Preferences

---

## Exit Criteria

* Users can authenticate from frontend
* Sessions persist correctly
* Protected routes work
* Google Login works end-to-end

---

# PHASE 3

# Core Healthcare Data Layer

## Objective

Implement remaining MongoDB collections, schemas, repositories, and services.

Include:

* doctor_profiles
* doctor_availability
* appointments
* payments
* consultations
* prescriptions
* reports
* reminders
* notifications
* chat_sessions
* chat_messages
* doctor_wallets
* doctor_documents
* health_insights
* notification_preferences
* agent_logs
* audit_logs

---

## Deliverables

* Models
* Schemas
* Repositories
* Services
* Indexes

---

## Exit Criteria

* CRUD foundation complete
* Service layer complete
* Database layer production-ready

---

# PHASE 4

# Dashboard System

## Objective

Implement dashboard data.

---

## Features

Patient Dashboard:

* Health Summary
* Reports
* Appointments
* Reminders

Doctor Dashboard:

* Appointments
* Earnings
* Patients

Admin Dashboard:

* Users
* Doctors
* Revenue

---

## Exit Criteria

```text
All dashboards load dynamic data
```

---

# PHASE 5

# Doctor Management System

## Objective

Enable doctor onboarding.

---

## Features

Doctor Registration

Doctor Verification

Availability Management

Doctor Profile

---

## Exit Criteria

```text
Doctors can manage slots
Admin can verify doctors
```

---

# PHASE 6

# Appointment Management

## Objective

Enable appointment booking.

---

## Flow

```text
Doctor Search
 ↓
Slot Selection
 ↓
Appointment Request
 ↓
Approval
 ↓
Consultation
```

---

## Features

* Book Appointment
* Cancel Appointment
* Approve Appointment
* Consultation History

---

## Exit Criteria

```text
Patients can book appointments
Doctors can approve appointments
```

---

# PHASE 6.5

# Administration & Platform Operations

## Objective

Create a production-ready administrative system.

All admins share the same permissions.
No Super Admin role.
Use a single ADMIN role.

---

## Sprint 1: Admin Bootstrap

### Features

* Initial Admin creation
* Environment bootstrap
* Startup initialization
* Admin login verification

### Environment Variables

```env
ADMIN_EMAIL=
ADMIN_PASSWORD=
ADMIN_NAME=
```

### Requirements

On application startup:
* If no admin exists: Create first admin automatically.
* If admin already exists: Skip creation.

Admin uses existing authentication system:
* Login
* Google Login
* Forgot Password
* Reset Password
* Refresh Tokens
* Session Management

### Deliverables

* Bootstrap service
* Startup initialization
* Seed mechanism
* Tests

### Exit Criteria

```text
Fresh deployment automatically creates first Admin.
```

---

## Sprint 2: Admin Management

### Features

* Create Admin
* List Admins
* View Admin
* Disable Admin
* Enable Admin

### Rules

* Any active admin can create another admin.
* Any active admin can disable another admin.
* Any active admin can re-enable another admin.
* Last remaining admin cannot be disabled.
* Last remaining admin cannot be deleted.

### Deliverables

* Admin APIs
* Admin management UI
* Tests

### Exit Criteria

```text
Admins can manage administrator accounts.
```

---

## Sprint 3: Admin Security & Recovery

### Features

* Admin Forgot Password
* Admin Reset Password
* Admin Session Management
* Admin Security Events
* Audit Logs

### Requirements

* Reuse existing authentication system (no separate admin auth implementation).
* All administrative actions create audit logs.

### Deliverables

* Security integrations
* Audit tracking
* Tests

### Exit Criteria

```text
Admins can securely recover access.
```

---

## Sprint 4: User & Doctor Operations

### Features

User Management:
* List Users
* Search Users
* View User
* Suspend User
* Activate User

Doctor Management:
* Pending Doctors
* Approved Doctors
* Rejected Doctors
* Suspended Doctors

Actions:
* Approve Doctor
* Reject Doctor
* Suspend Doctor
* Reactivate Doctor

### Deliverables

* Operations dashboard
* Management APIs
* Search & Filters
* Tests

### Exit Criteria

```text
Admins can operate platform users and doctors.
```

---

## Sprint 5: Platform Analytics

### Features

User Metrics:
* Total Users
* Active Users
* Growth Trends

Doctor Metrics:
* Total Doctors
* Verification Metrics
* Activity Metrics

Appointment Metrics:
* Pending
* Approved
* Completed
* Cancelled

Revenue Metrics:
* Doctor Earnings
* Platform Revenue
* Revenue Trends

Healthcare Metrics:
* Reports
* Consultations
* Prescriptions

### Deliverables

* Analytics APIs
* Analytics Dashboard
* Charts
* Tests

### Exit Criteria

```text
Admins can monitor platform health.
```

---

## Sprint 6: System Logs & Audit Center

### Objective

Provide administrators with complete visibility into platform activity through a centralized logging dashboard.

---

### Features

#### Audit Logs

* View all audit logs
* Search logs
* Pagination
* Filters:
  * User
  * Role
  * Action
  * Resource Type
  * Date Range
* View complete log details

#### Agent Logs

* View AI agent execution logs
* Filter by:
  * Agent
  * Status
  * Session
  * Date
* View execution metadata
* View execution duration

#### Authentication Logs

Display:
* Login
* Logout
* Password Reset
* Password Change
* Token Refresh
* Session Revocation
* Admin Security Events

#### Platform Events

Display:
* Doctor Verification
* Appointment Events
* Consultation Events
* Notification Events
* Report Processing
* Payment Events (future-ready)

---

### Backend Deliverables

* Log APIs
* Search
* Pagination
* Filtering
* Detail endpoints

---

### Frontend Deliverables

Create:
```
/dashboard/admin/logs
```

Tabs:
* Audit Logs
* Agent Logs
* Authentication Logs

Features:
* Search
* Filters
* Pagination
* Detail Drawer
* Copy JSON
* Export (future-ready)

---

### Exit Criteria

```text
Administrators can inspect all important platform events.
```

---

## Sprint 7: Doctor Patient Management

### Objective

Allow doctors to manage patients they have treated through appointments and consultations.

---

### Features

Patient Directory
* List Patients
* Search Patients
* Filters
* Patient Summary Cards

Patient Profile
* Basic Information
* Medical Overview
* Appointment History
* Consultation History
* Uploaded Reports
* Prescriptions
* Health Insights

Actions
* Open Chat
* View Reports
* View Consultation
* Future Follow-up Support

---

### Backend Deliverables

* Patient List APIs
* Patient Detail APIs
* Aggregated History APIs

---

### Frontend Deliverables

Create:
```
/dashboard/patients
```

Include:
* Patient List
* Patient Details
* Search
* Filters
* Empty States
* Loading States
* Error States

---

### Exit Criteria

```text
Doctors can manage all patients assigned to them.
```

---

## Sprint 8: Doctor Earnings & Wallet Dashboard

### Objective

Complete the doctor's financial dashboard before Razorpay integration.

This sprint must use the existing wallet infrastructure created in Phase 3 and be fully compatible with Phase 7 Payment System.

---

### Features

Wallet
* Available Balance
* Pending Balance
* Lifetime Earnings

Revenue
* Doctor Share
* Platform Share
* Revenue Split Summary

History
* Consultation Earnings
* Transaction History
* Payment Timeline
* Pending Payouts

Analytics
* Monthly Earnings
* Revenue Trends
* Consultation Revenue
* Wallet Summary

Future Ready
* Razorpay Transactions
* Withdrawals
* Settlements

---

### Backend Deliverables

* Earnings APIs
* Wallet APIs
* Revenue Summary APIs
* Transaction APIs

---

### Frontend Deliverables

Create:
```
/dashboard/earnings
```

Include:
* Earnings Dashboard
* Wallet Summary
* Charts
* Revenue Cards
* Transaction History
* Empty States
* Loading States
* Error States

---

### Exit Criteria

```text
Doctors can monitor earnings before payment integration.
```

---

## Sprint 9: Platform Monitoring & Maintenance

### Objective

Provide administrators with operational visibility into the health of the platform.

---

### Features

System Health
* API Status
* MongoDB Status
* Qdrant Status
* Groq Status
* Supabase Status
* Storage Status

Background Jobs
* Reminder Jobs
* Notification Jobs
* AI Jobs
* Failed Jobs

Maintenance
* Clear Expired Sessions
* Clear Expired OTPs
* Archive Notifications
* Archive Audit Logs

Platform Information
* Version
* Environment
* Startup Time
* Uptime

---

### Backend Deliverables

* Monitoring APIs
* Maintenance APIs
* Health APIs

---

### Frontend Deliverables

Create:
```
/dashboard/admin/system
```

Include:
* Health Dashboard
* Service Status Cards
* Maintenance Actions
* Job Monitor

---

### Exit Criteria

```text
Administrators can monitor platform health and perform maintenance.
```

---

## Acceptance Criteria

1. First administrator is automatically created on fresh deployment.
2. Administrators can login using the standard authentication flow.
3. Administrators can create additional administrators.
4. Administrators can securely recover their accounts.
5. Administrators can manage users.
6. Administrators can manage doctors.
7. Administrators can inspect audit logs.
8. Administrators can inspect AI agent logs.
9. Doctors can manage their patients.
10. Doctors can monitor wallet and earnings.
11. Administrators can monitor overall platform health.
12. Every dashboard navigation item implemented in completed phases resolves successfully without any 404 pages.
13. Phase 7 (Payment System) can build directly on this completed operational foundation.

---

# PHASE 7

# Payment System

## Objective

Integrate Razorpay.

---

## Features

```text
Create Order
Verify Payment
Transaction History
Revenue Split
Doctor Wallet
```

---

## Revenue Split

Example:

```text
Consultation Fee = ₹500

Doctor = ₹425
Platform = ₹75
```

---

## Exit Criteria

```text
Payments verified successfully
Revenue split recorded
```

---

# PHASE 8

# AI Infrastructure

## Objective

Build AI foundation.

---

## Setup

```text
Groq
LangGraph
Qdrant
Embedding Pipeline
```

---

## Deliverables

```text
LLM Service
Embedding Service
Vector Service
Agent Base Classes
Patient Context Builder
```

---

## Exit Criteria

```text
AI service can answer test queries
```

---

# PHASE 9

# Retrieval-Augmented Generation

## Objective

Implement RAG.

---

## Qdrant Collections

```text
patient_reports
medical_knowledge
drug_knowledge
chat_memory
doctor_knowledge
```

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

## Multi-Collection Retrieval

Retrieval occurs from multiple collections depending on detected intent.

Examples:
* Medical Question → `medical_knowledge`
* Report Question → `patient_reports`
* Drug Question → `drug_knowledge`
* Doctor Search → `doctor_knowledge`
* Conversation Recall → `chat_memory`
* Patient Summary → `patient_memory` (MongoDB)

The Retrieval Agent decides which collections to query.

---

## Memory Update Pipeline

Whenever an important healthcare event occurs:

```text
Event
 ↓
Extract structured data
 ↓
Generate summary
 ↓
Update patient_memory (MongoDB)
 ↓
Chunk relevant content
 ↓
Generate embeddings
 ↓
Update Qdrant
```

The system keeps MongoDB summaries synchronized with vector knowledge.

---

## Exit Criteria

```text
Relevant context retrieved
```

---

# PHASE 10

# Multi-Agent System

## Objective

Build LangGraph workflow.

---

## Agents

```text
Router Agent
Retrieval Agent

Symptom Agent
Medical Knowledge Agent
Report Analysis Agent
Drug Interaction Agent
Doctor Recommendation Agent
Reminder Agent
Appointment Agent

Memory Agent
```

---

## Workflow

```text
Intent Detection
 ↓
Retrieval
 ↓
Routing
 ↓
Agent Execution
 ↓
Response
```

---

## Exit Criteria

```text
Agents route correctly
```

---

# PHASE 11

# Report Analysis

## Objective

Analyze uploaded reports.

---

## Workflow

```text
Upload
↓
OCR
↓
Structured Extraction
↓
Entity Extraction
↓
Risk Detection
↓
Chunking
↓
Embeddings
↓
Qdrant
↓
AI Analysis
```

---

## Features

* OCR
* Summarization
* Risk Detection
* Trend Analysis

---

## Exit Criteria

```text
Reports generate summaries
```

---

# PHASE 12

# Drug Safety

## Objective

Medication safety validation.

---

## Workflow

```text
Drug Input
 ↓
RxNorm
 ↓
Dataset Lookup
 ↓
Risk Classification
 ↓
Recommendation
```

---

## Risk Levels

```text
Low
Medium
High
```

---

## Reminder Integration

```text
Reminder Creation
 ↓
Interaction Check
 ↓
Validation
 ↓
Reminder Stored
```

---

## Exit Criteria

```text
Interactions detected correctly
```

---

# PHASE 13

# Testing & Deployment

## Objective

Deploy production-ready platform.

---

## Testing

Backend:

* Unit Tests
* Integration Tests

Frontend:

* Component Tests
* Flow Tests

AI:

* Agent Testing
* RAG Testing

---

## Deployment

Frontend:

```text
Vercel
```

Backend:

```text
Railway
```

Services:

```text
MongoDB Atlas
Qdrant Cloud
Groq
Supabase Storage
Razorpay
```

---

# Final MVP Features

## Authentication

* Register
* Login
* Google Login
* Forgot Password

## Patient

* Dashboard
* Reports
* Chat
* Reminders
* Doctors
* Appointments

## Doctor

* Dashboard
* Patients
* Appointments
* Availability
* Earnings

## Admin

* Initial Admin Bootstrap
* Admin Lifecycle Management (Create, List, Disable, Enable Admins)
* User Management (List, Search, Suspend, Activate Users)
* Doctor Management & Verification (Pending, Approve, Reject, Suspend, Reactivate Doctors)
* Platform Analytics (User, Doctor, Appointment, Revenue, and Healthcare metrics)
* Audit Logging of all Administrative Actions

## AI

* Symptom Analysis
* Medical Questions
* Report Analysis
* Drug Interaction Checks
* Doctor Recommendations

## Healthcare

* Appointment Booking
* Consultation Tracking
* Prescription Management
* Reminder Management

---

# Production Readiness Checklist

* JWT Authentication
* RBAC Authorization
* Input Validation
* Secure APIs
* Error Handling
* Logging
* Monitoring
* Environment Management
* CI/CD Ready
* Cloud Deployment Ready

---

# Definition of Done

Nura is considered MVP complete when:

* Users can register and login
* Reports can be uploaded and analyzed
* Appointments can be booked and managed
* Payments are processed successfully
* Drug interactions are detected
* Reminders are managed
* AI chatbot uses RAG and patient context
* Multi-agent architecture functions correctly
* Administrative operations and bootstrap function correctly
* Application is deployed and accessible
