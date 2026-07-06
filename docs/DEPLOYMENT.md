# Deployment Guide - Storage & Configuration

This guide details the deployment steps required to configure and run the Nura file storage subsystem in production.

## 1. Environment Configurations

In the production environment (e.g., Vercel, Render, Heroku), ensure the following environment variables are set:

```env
# Define the active storage provider
STORAGE_PROVIDER=supabase

# Base Supabase Credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Backend base URL for legacy lookups
BACKEND_URL=https://api.nura-health.com
```

---

## 2. Supabase Storage Buckets Setup

The backend automatically attempts to verify and create buckets upon initial upload, but we recommend pre-configuring them in the Supabase Console.

Configure the three storage buckets:

### 1. `avatars`
* **Visibility**: Public (Check `Public bucket` in Supabase UI)
* **Access Policy (RLS)**:
  * Select/Read: `Allowed for everyone` (Public)
  * Insert/Update/Delete: Restrict to `authenticated` or backend service-role.

### 2. `reports`
* **Visibility**: Private (Uncheck `Public bucket` in Supabase UI)
* **Access Policy (RLS)**:
  * Select/Read: Restrict to `authenticated` or backend service-role (Access happens via signed URLs).
  * Insert/Update/Delete: Restrict to backend service-role only.

### 3. `doctor-documents`
* **Visibility**: Private (Uncheck `Public bucket` in Supabase UI)
* **Access Policy (RLS)**:
  * Select/Read: Restrict to backend service-role / admins.
  * Insert/Update/Delete: Restrict to backend service-role only.

---

## 3. Storage Migration Process

To migrate existing uploads from local storage to Supabase during deployment, run the migration utility script.

### Pre-requisites
1. Set the destination credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`) in the environment or active `.env` file.
2. Ensure MongoDB connection (`MONGODB_URL`) points to the correct production database.

### Running Migration
Execute the migration script from the backend directory:

```bash
cd backend
python scripts/migrate_local_storage_to_supabase.py
```

The script will scan `users`, `reports`, and `doctor_documents` collections, copy local files, verify SHA-256 checksums, and print the detailed execution summary report.
