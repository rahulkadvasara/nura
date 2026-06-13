# Nura - Setup Guide

## 1. Purpose

This document describes how to set up the Nura development environment.

It covers:

* Prerequisites
* Project setup
* Environment configuration
* Backend startup
* Frontend startup
* Third-party services
* Docker setup

This guide should allow a new developer to run Nura locally with minimal effort.

---

# 2. System Requirements

Recommended:

| Component      | Version |
| -------------- | ------- |
| Python         | 3.12+   |
| Node.js        | 22+     |
| npm            | 10+     |
| Git            | Latest  |
| Docker         | Latest  |
| Docker Compose | Latest  |

---

# 3. Clone Repository

```bash
git clone https://github.com/your-org/nura-ai.git

cd nura-ai
```

---

# 4. Project Structure

```text
nura-ai/

├── frontend/
├── backend/
├── docs/
```

---

# 5. Third-Party Services

Before running Nura, create the following services.

---

## MongoDB Atlas

Create:

```text
Project: Nura
```

Collect:

```text
MONGODB_URL
```

---

## Qdrant Cloud

Create:

```text
Cluster: nura
```

Collect:

```text
QDRANT_URL
QDRANT_API_KEY
```

---

## Groq Cloud

Generate:

```text
GROQ_API_KEY
```

---

## Google OAuth

Create OAuth credentials.

Collect:

```text
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

---

## Brevo SMTP

Collect:

```text
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
```

---

## Supabase

Create:

```text
Project: nura
```

Create Bucket:

```text
medical-files
```

Collect:

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

---

## Razorpay

Required later.

Can be skipped during Phase 0 and Phase 1.

Collect when needed:

```text
RAZORPAY_KEY_ID
RAZORPAY_KEY_SECRET
```

---

# 6. Backend Setup

Navigate:

```bash
cd backend
```

---

## Create Virtual Environment

Windows:

```bash
python -m venv venv

venv\Scripts\activate
```

Mac/Linux:

```bash
python3 -m venv venv

source venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Create Environment File

Create:

```text
backend/.env
```

Copy values from:

```text
backend/.env.example
```

Fill all required variables.

---

# 7. Frontend Setup

Navigate:

```bash
cd frontend
```

---

## Install Dependencies

```bash
npm install
```

---

## Create Environment File

Create:

```text
frontend/.env.local
```

Copy values from:

```text
frontend/.env.example
```

Fill all required variables.

---

# 8. Generate Secret Key

Run:

```python
import secrets

print(secrets.token_urlsafe(64))
```

Copy output into:

```env
SECRET_KEY=
```

---

# 9. Verify Environment Variables

Backend variables:

```text
APP_NAME
APP_ENV

SECRET_KEY

JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS

FRONTEND_URL

API_V1_PREFIX

LOG_LEVEL

MONGODB_URL
MONGODB_DATABASE

QDRANT_URL
QDRANT_API_KEY

GROQ_API_KEY

GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET

SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD

SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_BUCKET

BACKEND_CORS_ORIGINS

EMBEDDING_MODEL
```

---

Frontend variables:

```text
NEXT_PUBLIC_API_URL

NEXT_PUBLIC_APP_NAME

NEXT_PUBLIC_GOOGLE_CLIENT_ID

NEXT_PUBLIC_RAZORPAY_KEY_ID
```

---

# 10. Run Backend

Navigate:

```bash
cd backend
```

Start:

```bash
uvicorn app.main:app --reload
```

Expected:

```text
http://localhost:8000
```

---

## Verify Health Endpoint

Open:

```text
http://localhost:8000/api/v1/health
```

Expected:

```json
{
  "status": "healthy",
  "mongodb": "connected",
  "qdrant": "connected"
}
```

---

# 11. Run Frontend

Navigate:

```bash
cd frontend
```

Start:

```bash
npm run dev
```

Expected:

```text
http://localhost:3000
```

---

# 12. Docker Setup

From project root:

```bash
docker compose up --build
```

Services:

```text
frontend
backend
```

MongoDB Atlas and Qdrant Cloud remain external.

---

# 13. Development Workflow

Recommended order:

```text
Phase 0
↓
Authentication
↓
Database Models
↓
Dashboard
↓
Doctor System
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
Testing
↓
Deployment
```

---

# 14. Troubleshooting

## MongoDB Connection Error

Check:

```text
MONGODB_URL
IP Whitelist
Database User Permissions
```

---

## Qdrant Connection Error

Check:

```text
QDRANT_URL
QDRANT_API_KEY
```

---

## OAuth Error

Check:

```text
Authorized Redirect URI
GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET
```

---

## Email Not Sending

Check:

```text
SMTP_HOST
SMTP_PORT
SMTP_USER
SMTP_PASSWORD
```

---

## Supabase Upload Error

Check:

```text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
Bucket Permissions
```

---

# 15. Development Standards

Backend:

```text
Black
isort
ruff
pytest
```

Frontend:

```text
ESLint
Prettier
TypeScript Strict Mode
```

---

# 16. Security Rules

Never commit:

```text
.env
.env.local
```

Never expose:

```text
SECRET_KEY
API Keys
Service Role Keys
```

Use:

```text
.env.example
```

for documentation.

---

# 17. Phase 0 Exit Criteria

Phase 0 is complete when:

```text
✓ Frontend starts successfully

✓ Backend starts successfully

✓ MongoDB connected

✓ Qdrant connected

✓ Health endpoint operational

✓ Environment variables configured

✓ Docker builds successfully
```

---

# 18. Definition of Done

Nura setup is considered complete when a developer can:

* Clone repository
* Configure environment variables
* Start frontend
* Start backend
* Connect MongoDB Atlas
* Connect Qdrant Cloud
* Access health endpoint
* Begin Phase 1 development without additional infrastructure work

```
```
