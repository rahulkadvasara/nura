# Nura Deployment & Environment Switching Guide

This document provides complete instructions for deploying the **Nura** application:
- **Frontend**: Next.js deployed on **Vercel**
- **Backend**: FastAPI deployed on **Render**

It also explains how to seamlessly toggle between **Local Development** mode and **Production Server** mode.

---

## 1. Quick Link & URL Checklist (Post-Deployment Wire-up)

When deploying for the first time, you will obtain live production URLs from Render and Vercel. Here is where you paste them:

| Source Platform | Generated URL Example | Target Setting / Variable | Where to Update |
| :--- | :--- | :--- | :--- |
| **Render** (Backend) | `https://nura-backend.onrender.com` | `NEXT_PUBLIC_API_URL` | Vercel Environment Variables: `https://nura-backend.onrender.com/api/v1` |
| **Render** (Backend) | `https://nura-backend.onrender.com` | `BACKEND_URL` | Render Environment Variables: `https://nura-backend.onrender.com` |
| **Render** (Backend) | `https://nura-backend.onrender.com` | `GOOGLE_MEET_REDIRECT_URI` | Render Env: `https://nura-backend.onrender.com/api/v1/integrations/google/callback` |
| **Vercel** (Frontend) | `https://nura-frontend.vercel.app` | `FRONTEND_URL` | Render Environment Variables: `https://nura-frontend.vercel.app` |
| **Vercel** (Frontend) | `https://nura-frontend.vercel.app` | `BACKEND_CORS_ORIGINS` | Render Environment Variables: `https://nura-frontend.vercel.app` |
| **Google Cloud Console** | - | Authorized JavaScript Origins | `https://nura-frontend.vercel.app` |
| **Google Cloud Console** | - | Authorized Redirect URIs | `https://nura-backend.onrender.com/api/v1/integrations/google/callback` |

---

## 2. Step-by-Step Backend Deployment on Render

### Step 2.1: Create a Render Web Service
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Connect your Git repository (`nura`).
4. Configure service settings:
   - **Name**: `nura-backend` (or your preferred service name)
   - **Region**: Choose closest to your database (e.g. Oregon/Frankfurt)
   - **Branch**: `main` or `dev`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 2.2: Add Environment Variables on Render
Under **Environment Variables** in Render, add the following key-value pairs:

```env
APP_NAME=Nura
APP_ENV=production
SECRET_KEY=<>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Production Frontend URL (Update once Vercel finishes deploying)
FRONTEND_URL=https://<YOUR-VERCEL-FRONTEND-URL>.vercel.app
BACKEND_CORS_ORIGINS=https://<YOUR-VERCEL-FRONTEND-URL>.vercel.app

API_V1_PREFIX=/api/v1
LOG_LEVEL=INFO

# Databases
MONGODB_URL=<>
MONGODB_DATABASE=<>

QDRANT_URL=https://73274c2a-718a-4d0b-a090-c9edbb83241d.eu-central-1-0.aws.cloud.qdrant.io
QDRANT_API_KEY=<>
CLUSTER_ID=<>

# AI Services
GROQ_API_KEY=<>
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BACKUP_MODEL=openai/gpt-oss-20b
GROQ_CLASSIFIER_MODEL=openai/gpt-oss-20b
MODEL_OPENAI_120B=openai/gpt-oss-120b
MODEL_OPENAI_20B=openai/gpt-oss-20b

# OAuth Credentials
GOOGLE_CLIENT_ID=<>
GOOGLE_CLIENT_SECRET=<>
GOOGLE_MEET_CLIENT_ID=<>
GOOGLE_MEET_CLIENT_SECRET=<>
GOOGLE_MEET_REDIRECT_URI=https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/api/v1/integrations/google/callback

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=kadvasararahul@gmail.com
SMTP_PASSWORD=<>

# Supabase Storage
SUPABASE_URL=https://vdhdwfdrtiipyfuyvdyk.supabase.co
SUPABASE_ANON_KEY=<>
SUPABASE_SERVICE_ROLE_KEY=<>
SUPABASE_BUCKET=medical-files
STORAGE_PROVIDER=supabase
BACKEND_URL=https://<YOUR-RENDER-BACKEND-NAME>.onrender.com

# Razorpay
RAZORPAY_KEY_ID=<>
RAZORPAY_KEY_SECRET=<>

# Admin Bootstrap
ADMIN_EMAIL=<>
ADMIN_PASSWORD=<>
ADMIN_NAME=<>
```

5. Click **Create Web Service**. Once deployment succeeds, copy your Render URL (e.g. `https://nura-backend.onrender.com`).

---

## 3. Step-by-Step Frontend Deployment on Vercel

### Step 3.1: Import Project into Vercel
1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your Git repository (`nura`).
4. Configure Project Settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: Click Edit and select `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Step 3.2: Add Environment Variables on Vercel
In the Vercel project environment configuration section, add:

```env
# Point this to your live Render Backend URL + /api/v1
NEXT_PUBLIC_API_URL=https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/api/v1

NEXT_PUBLIC_APP_NAME=Nura
NEXT_PUBLIC_GOOGLE_CLIENT_ID=185422838122-7g7mfjodao4ov7kkclagm3uirqi38ol5.apps.googleusercontent.com
NEXT_PUBLIC_RAZORPAY_KEY_ID=rzp_test_T5rgFC29hflpNx
```

3. Click **Deploy**. Vercel will build and assign a URL (e.g. `https://nura-frontend.vercel.app`).

---

## 4. How to Switch Between Local and Server (Production)

### A. Switching to Production Mode (Server)

1. **Frontend (`frontend/.env.local`)**:
   Comment out local and set the Render URL:
   ```env
   # Local Development:
   # NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

   # Production (Render Backend):
   NEXT_PUBLIC_API_URL=https://nura-backend.onrender.com/api/v1
   ```

2. **Backend (`backend/.env`)**:
   Comment out local URLs and set Vercel frontend URL & Render backend URL:
   ```env
   APP_ENV=production

   # Local Development:
   # FRONTEND_URL=http://localhost:3000
   # BACKEND_CORS_ORIGINS=http://localhost:3000
   # BACKEND_URL=http://localhost:8000
   # GOOGLE_MEET_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

   # Production:
   FRONTEND_URL=https://nura-frontend.vercel.app
   BACKEND_CORS_ORIGINS=https://nura-frontend.vercel.app
   BACKEND_URL=https://nura-backend.onrender.com
   GOOGLE_MEET_REDIRECT_URI=https://nura-backend.onrender.com/api/v1/integrations/google/callback
   ```

---

### B. Switching Back to Local Development Mode

1. **Frontend (`frontend/.env.local`)**:
   Uncomment `http://localhost:8000/api/v1`:
   ```env
   # Local Development:
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

   # Production (Render Backend):
   # NEXT_PUBLIC_API_URL=https://nura-backend.onrender.com/api/v1
   ```

2. **Backend (`backend/.env`)**:
   Uncomment local environment settings:
   ```env
   APP_ENV=development

   # Local Development:
   FRONTEND_URL=http://localhost:3000
   BACKEND_CORS_ORIGINS=http://localhost:3000
   BACKEND_URL=http://localhost:8000
   GOOGLE_MEET_REDIRECT_URI=http://localhost:8000/api/v1/integrations/google/callback

   # Production:
   # FRONTEND_URL=https://nura-frontend.vercel.app
   # BACKEND_CORS_ORIGINS=https://nura-frontend.vercel.app
   # BACKEND_URL=https://nura-backend.onrender.com
   # GOOGLE_MEET_REDIRECT_URI=https://nura-backend.onrender.com/api/v1/integrations/google/callback
   ```

---

## 5. Verification & Testing

Once deployed:
1. Open the Vercel URL in your browser: `https://<YOUR-VERCEL-FRONTEND-URL>.vercel.app`.
2. Check network requests in Developer Tools (F12) to verify requests reach `https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/api/v1`.
3. Check Backend Health endpoint: `https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/api/v1/health`.
4. Check Swagger API docs: `https://<YOUR-RENDER-BACKEND-NAME>.onrender.com/docs`.
