# Nura - Implementation Plan

# 1. Purpose

This document defines the development roadmap for Nura.

The goal is to build the platform incrementally while maintaining a production-ready architecture.

Each phase should result in a stable and testable system.

---

# 2. Development Strategy

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

# 3. Milestone Overview

| Phase    | Name                 | Duration |
| -------- | -------------------- | -------- |
| Phase 0  | Project Setup        | 1 Day    |
| Phase 1  | Authentication       | 2-3 Days |
| Phase 2  | Database & CRUD      | 2-3 Days |
| Phase 3  | Dashboard            | 1-2 Days |
| Phase 4  | Doctor System        | 2 Days   |
| Phase 5  | Appointment System   | 2 Days   |
| Phase 6  | Payment System       | 1 Day    |
| Phase 7  | AI Infrastructure    | 2 Days   |
| Phase 8  | RAG System           | 2 Days   |
| Phase 9  | Multi-Agent System   | 3 Days   |
| Phase 10 | Report Analysis      | 2 Days   |
| Phase 11 | Drug Safety          | 2 Days   |
| Phase 12 | Testing & Deployment | 2 Days   |

Estimated MVP:

```text
20 - 25 Days
```

---

# PHASE 0

# Project Setup

## Objective

Create project foundation.

---

## Deliverables

```text
frontend/
backend/
docs/
```

---

## Frontend Setup

Tech Stack:

```text
Next.js 15
TypeScript
Tailwind CSS
shadcn/ui
TanStack Query
Zustand
```

Tasks:

* Initialize Next.js
* Configure Tailwind
* Configure shadcn/ui
* Setup routing
* Setup layouts

---

## Backend Setup

Tech Stack:

```text
FastAPI
MongoDB
Qdrant
```

Tasks:

* Create folder structure
* Configure environment variables
* Configure MongoDB
* Configure Qdrant
* Configure logging

---

# Exit Criteria

```text
Frontend runs
Backend runs
Mongo connected
Qdrant connected
```

---

# PHASE 1

# Authentication System

## Objective

Build secure authentication.

---

## Features

### Registration

```text
Email
Password
OTP Verification
```

### Login

```text
Email
Password
```

### Google OAuth

```text
Google Login
```

### Password Recovery

```text
Forgot Password
Reset Password
```

---

## Deliverables

Backend:

```text
Auth APIs
JWT
Role Middleware
```

Frontend:

```text
Register
Login
Forgot Password
```

---

# Exit Criteria

```text
Users can register
Users can login
JWT works
Google OAuth works
```

---

# PHASE 2

# Database Models

## Objective

Implement all collections.

Collections:

```text
users
doctor_profiles
doctor_availability
appointments
payments
consultations
prescriptions
reports
reminders
notifications
chat_sessions
chat_messages
doctor_wallets
drug_interactions
audit_logs
```

---

## Deliverables

```text
Models
Schemas
Repositories
Indexes
```

---

# Exit Criteria

```text
CRUD works for all collections
```

---

# PHASE 3

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

# PHASE 4

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

# PHASE 5

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

# PHASE 6

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

# PHASE 7

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
```

---

## Exit Criteria

```text
AI service can answer test queries
```

---

# PHASE 8

# Retrieval-Augmented Generation

## Objective

Implement RAG.

---

## Qdrant Collections

```text
patient_reports
chat_memory
medical_knowledge
drug_knowledge
```

---

## Workflow

```text
Query
 ↓
Embedding
 ↓
Vector Search
 ↓
Context Assembly
 ↓
Prompt Construction
```

---

## Exit Criteria

```text
Relevant context retrieved
```

---

# PHASE 9

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

# PHASE 10

# Report Analysis System

## Objective

Analyze uploaded reports.

---

## Workflow

```text
Upload
 ↓
OCR
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

# PHASE 11

# Drug Safety System

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

# PHASE 12

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

* Doctor Verification
* Analytics
* User Management

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
* Application is deployed and accessible
