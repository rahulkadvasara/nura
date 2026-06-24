# Nura - Environment Variables Guide

## 1. Purpose

This document defines all environment variables used by Nura.

It serves as the single source of truth for:

* Backend configuration
* Frontend configuration
* Database connections
* AI integrations
* Authentication
* Email services
* Storage services
* Payments

---

# 2. Environment Strategy

Nura uses separate environment files.

Backend:

```text
backend/.env
backend/.env.example
```

Frontend:

```text
frontend/.env.local
frontend/.env.example
```

---

# 3. Backend Environment Variables

## Application

### APP_NAME

Application name.

Example:

```env
APP_NAME=Nura
```

---

### APP_ENV

Current environment.

Allowed Values:

```text
development
staging
production
```

Example:

```env
APP_ENV=development
```

---

### API_V1_PREFIX

API version prefix.

Example:

```env
API_V1_PREFIX=/api/v1
```

---

### LOG_LEVEL

Application logging level.

Allowed Values:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Example:

```env
LOG_LEVEL=INFO
```

---

# 4. Security Variables

## SECRET_KEY

JWT signing secret.

Generate:

```python
import secrets
print(secrets.token_urlsafe(64))
```

Example:

```env
SECRET_KEY=YOUR_SECRET_KEY
```

---

## JWT_ALGORITHM

JWT signing algorithm.

Example:

```env
JWT_ALGORITHM=HS256
```

---

## ACCESS_TOKEN_EXPIRE_MINUTES

Access token expiry.

Example:

```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## REFRESH_TOKEN_EXPIRE_DAYS

Refresh token expiry.

Example:

```env
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

# 5. Frontend Communication

## FRONTEND_URL

Frontend origin.

Development:

```env
FRONTEND_URL=http://localhost:3000
```

Production:

```env
FRONTEND_URL=https://nura.app
```

---

## BACKEND_CORS_ORIGINS

Allowed frontend origins.

Development:

```env
BACKEND_CORS_ORIGINS=http://localhost:3000
```

Production:

```env
BACKEND_CORS_ORIGINS=https://nura.app
```

---

# 6. MongoDB

## MONGODB_URL

MongoDB Atlas connection string.

Example:

```env
MONGODB_URL=mongodb+srv://...
```

---

## MONGODB_DATABASE

Database name.

Example:

```env
MONGODB_DATABASE=nura
```

---

# 7. Qdrant

## QDRANT_URL

Qdrant Cloud URL.

Example:

```env
QDRANT_URL=https://xxxx.qdrant.tech
```

---

## QDRANT_API_KEY

Qdrant API key.

Example:

```env
QDRANT_API_KEY=xxxxxxxx
```

---

# 8. Groq

## GROQ_API_KEY

Groq API key.

Example:

```env
GROQ_API_KEY=gsk_xxxxxxxxx
```

---

# 9. Embeddings

## EMBEDDING_MODEL

Embedding model used throughout the platform.

Recommended:

```env
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

Used For:

```text
Report Embeddings
Chat Memory
Medical Knowledge
Drug Interactions
Doctor Knowledge
```

---

# 10. Google OAuth

## GOOGLE_CLIENT_ID

Google OAuth Client ID.

Example:

```env
GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
```

---

## GOOGLE_CLIENT_SECRET

Google OAuth Client Secret.

Example:

```env
GOOGLE_CLIENT_SECRET=xxxxxxxx
```

---

# 11. Email Service (Brevo)

## SMTP_HOST

Example:

```env
SMTP_HOST=smtp-relay.brevo.com
```

---

## SMTP_PORT

Example:

```env
SMTP_PORT=587
```

---

## SMTP_USER

Example:

```env
SMTP_USER=ae9a59001@smtp-brevo.com
```

---

## SMTP_PASSWORD

Brevo SMTP key.

Example:

```env
SMTP_PASSWORD=xxxxxxxx
```

---

# 12. Supabase Storage

## SUPABASE_URL

Supabase project URL.

Example:

```env
SUPABASE_URL=https://xxxx.supabase.co
```

---

## SUPABASE_ANON_KEY

Public key.

Example:

```env
SUPABASE_ANON_KEY=xxxxxxxx
```

---

## SUPABASE_SERVICE_ROLE_KEY

Server-side key.

Example:

```env
SUPABASE_SERVICE_ROLE_KEY=xxxxxxxx
```

---

## SUPABASE_BUCKET

Storage bucket.

Example:

```env
SUPABASE_BUCKET=medical-files
```

---

# 13. Razorpay

## RAZORPAY_KEY_ID

Example:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxx
```

---

## RAZORPAY_KEY_SECRET

Example:

```env
RAZORPAY_KEY_SECRET=xxxxxxxx
```

---

# 13.5 Admin Bootstrap

## ADMIN_EMAIL

Default initial admin email.

Example:

```env
ADMIN_EMAIL=admin@nura.app
```

---

## ADMIN_PASSWORD

Default initial admin password.

Example:

```env
ADMIN_PASSWORD=SecurePassword123!
```

---

## ADMIN_NAME

Default initial admin full name.

Example:

```env
ADMIN_NAME=Platform Administrator
```

---

# 14. Frontend Environment Variables

## NEXT_PUBLIC_API_URL

Backend API URL.

Development:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Production:

```env
NEXT_PUBLIC_API_URL=https://api.nura.app/api/v1
```

---

## NEXT_PUBLIC_APP_NAME

Application name.

Example:

```env
NEXT_PUBLIC_APP_NAME=Nura
```

---

## NEXT_PUBLIC_GOOGLE_CLIENT_ID

Google Client ID.

Example:

```env
NEXT_PUBLIC_GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
```

---

## NEXT_PUBLIC_RAZORPAY_KEY_ID

Public Razorpay key.

Example:

```env
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_xxxxx
```

---

# 15. Secrets Management Rules

Never commit:

```text
.env
.env.local
```

to Git.

Only commit:

```text
.env.example
```

files.

---

# 16. Production Secrets

Production secrets must be stored in:

```text
Vercel Environment Variables

Railway Environment Variables
```

Never hardcode secrets.

---

# 17. Required Variables Checklist

## Backend

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

ADMIN_EMAIL
ADMIN_PASSWORD
ADMIN_NAME
```

---

## Frontend

```text
NEXT_PUBLIC_API_URL

NEXT_PUBLIC_APP_NAME

NEXT_PUBLIC_GOOGLE_CLIENT_ID

NEXT_PUBLIC_RAZORPAY_KEY_ID
```

---

# 18. Definition of Done

Environment configuration is considered complete when:

* All required variables exist
* `.env.example` files are created
* Secrets are excluded from Git
* Development and production values are documented
* Frontend and backend variables are synchronized
* Third-party integrations can authenticate successfully

```
```
