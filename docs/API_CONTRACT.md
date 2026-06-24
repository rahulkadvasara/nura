# Nura - API Contract

## 1. Purpose

This document defines the API contract between the frontend and backend.

It serves as the source of truth for:

* Endpoints
* Request payloads
* Response payloads
* Error handling
* Authentication requirements

Base URL:

```text
/api/v1
```

---

# 2. API Standards

## Content Type

```http
Content-Type: application/json
```

---

## Success Response Format

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

---

## Error Response Format

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": []
}
```

---

## Pagination Format

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10
  }
}
```

---

# 3. Authentication APIs

## Register

### Endpoint

```http
POST /auth/register
```

### Request

```json
{
  "full_name": "Rahul",
  "email": "rahul@example.com",
  "password": "Password123!"
}
```

### Response

```json
{
  "success": true,
  "message": "OTP sent successfully"
}
```

---

## Verify OTP

### Endpoint

```http
POST /auth/verify-otp
```

### Request

```json
{
  "email": "rahul@example.com",
  "otp": "123456"
}
```

### Response

```json
{
  "success": true,
  "message": "Account verified"
}
```

---

## Login

### Endpoint

```http
POST /auth/login
```

### Request

```json
{
  "email": "rahul@example.com",
  "password": "Password123!"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "jwt",
    "refresh_token": "jwt",
    "user": {
      "id": "user_id",
      "role": "patient"
    }
  }
}
```

---

## Refresh Token

### Endpoint

```http
POST /auth/refresh
```

### Request

```json
{
  "refresh_token": "jwt"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt"
  }
}
```

---

## Logout

### Endpoint

```http
POST /auth/logout
```

### Response

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## Forgot Password

### Endpoint

```http
POST /auth/forgot-password
```

### Request

```json
{
  "email": "rahul@example.com"
}
```

---

## Reset Password

### Endpoint

```http
POST /auth/reset-password
```

### Request

```json
{
  "email": "rahul@example.com",
  "otp": "123456",
  "new_password": "Password123!"
}
```

---

## Current User

### Endpoint

```http
GET /auth/me
```

### Authentication

Required

---

# 4. User APIs

## Get Profile

```http
GET /users/profile
```

---

## Update Profile

```http
PUT /users/profile
```

### Request

```json
{
  "full_name": "Rahul",
  "phone": "+91XXXXXXXXXX"
}
```

---

## Patient Dashboard

```http
GET /users/dashboard
```

### Response

```json
{
  "success": true,
  "data": {
    "health_summary": {},
    "appointments": [],
    "reports": [],
    "reminders": [],
    "insights": []
  }
}
```

---

# 5. Doctor APIs

## List Doctors

```http
GET /doctors
```

### Query Parameters

```text
specialty
experience
fee_min
fee_max
availability
page
limit
```

---

## Doctor Details

```http
GET /doctors/{doctor_id}
```

---

## Create Availability

```http
POST /doctors/availability
```

### Request

```json
{
  "available_date": "2026-06-15",
  "start_time": "09:00",
  "end_time": "09:30"
}
```

---

## Update Availability

```http
PUT /doctors/availability/{availability_id}
```

---

## Delete Availability

```http
DELETE /doctors/availability/{availability_id}
```

---

# 6. Appointment APIs

## Create Appointment

```http
POST /appointments
```

### Request

```json
{
  "doctor_id": "doctor_id",
  "availability_id": "slot_id",
  "reason": "General consultation"
}
```

---

## List Appointments

```http
GET /appointments
```

---

## Appointment Details

```http
GET /appointments/{appointment_id}
```

---

## Approve Appointment

```http
POST /appointments/{appointment_id}/approve
```

---

## Reject Appointment

```http
POST /appointments/{appointment_id}/reject
```

---

## Cancel Appointment

```http
POST /appointments/{appointment_id}/cancel
```

---

# 7. Payment APIs

## Create Razorpay Order

```http
POST /payments/create-order
```

### Request

```json
{
  "appointment_id": "appointment_id"
}
```

---

## Verify Payment

```http
POST /payments/verify
```

### Request

```json
{
  "razorpay_order_id": "",
  "razorpay_payment_id": "",
  "razorpay_signature": ""
}
```

---

## Payment History

```http
GET /payments/history
```

---

# 8. Report APIs

## Upload Report

```http
POST /reports/upload
```

### Content Type

```http
multipart/form-data
```

### Fields

```text
file
```

---

## List Reports

```http
GET /reports
```

---

## Report Details

```http
GET /reports/{report_id}
```

---

## Delete Report

```http
DELETE /reports/{report_id}
```

---

## Report Analysis

```http
GET /reports/{report_id}/analysis
```

### Response

```json
{
  "summary": "",
  "risk_level": "medium",
  "entities": [],
  "recommendations": [],
  "insights": []
}
```

---

# 9. Reminder APIs

## Create Reminder

```http
POST /reminders
```

### Request

```json
{
  "title": "Vitamin D",
  "description": "Take after breakfast",
  "reminder_time": "08:00",
  "repeat_type": "daily"
}
```

---

## List Reminders

```http
GET /reminders
```

---

## Update Reminder

```http
PUT /reminders/{reminder_id}
```

---

## Delete Reminder

```http
DELETE /reminders/{reminder_id}
```

---

# 10. Chat APIs

## Send Message

```http
POST /chat/message
```

### Request

```json
{
  "session_id": "session_id",
  "message": "What does my blood report mean?"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "response": "",
    "agent": "ReportAnalysisAgent",
    "sources": []
  }
}
```

---

## Create Chat Session

```http
POST /chat/session
```

---

## List Chat Sessions

```http
GET /chat/sessions
```

---

## Session Messages

```http
GET /chat/session/{session_id}
```

---

# 11. Notification APIs

## Get Notifications

```http
GET /notifications
```

---

## Mark As Read

```http
POST /notifications/{notification_id}/read
```

---

## Notification Preferences

```http
GET /notifications/preferences
```

---

## Update Preferences

```http
PUT /notifications/preferences
```

---

# 12. Admin APIs

## Create Admin Account

```http
POST /admin/accounts
```

### Request

```json
{
  "full_name": "Admin Name",
  "email": "admin2@example.com",
  "password": "Password123!"
}
```

### Response

```json
{
  "success": true,
  "message": "Admin account created successfully",
  "data": {
    "id": "admin_id",
    "email": "admin2@example.com",
    "full_name": "Admin Name",
    "role": "admin",
    "is_active": true
  }
}
```

---

## List Admin Accounts

```http
GET /admin/accounts
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "admin_id",
      "email": "admin@example.com",
      "full_name": "Admin Name",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-06-24T12:00:00Z"
    }
  ]
}
```

---

## View Admin Account

```http
GET /admin/accounts/{admin_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "admin_id",
    "email": "admin@example.com",
    "full_name": "Admin Name",
    "role": "admin",
    "is_active": true,
    "created_at": "2026-06-24T12:00:00Z"
  }
}
```

---

## Disable Admin Account

```http
POST /admin/accounts/{admin_id}/disable
```

### Response

```json
{
  "success": true,
  "message": "Admin account disabled successfully"
}
```

---

## Enable Admin Account

```http
POST /admin/accounts/{admin_id}/enable
```

### Response

```json
{
  "success": true,
  "message": "Admin account enabled successfully"
}
```

---

## List Users

```http
GET /admin/users
```

### Query Parameters

```text
query (search full_name or email)
status (active|suspended)
page
limit
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "user_id",
      "email": "user@example.com",
      "full_name": "Patient Name",
      "role": "patient",
      "is_active": true,
      "created_at": "2026-06-24T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

---

## View User Details

```http
GET /admin/users/{user_id}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "user_id",
    "email": "user@example.com",
    "full_name": "Patient Name",
    "role": "patient",
    "is_active": true,
    "created_at": "2026-06-24T12:00:00Z"
  }
}
```

---

## Suspend User

```http
POST /admin/users/{user_id}/suspend
```

### Request

```json
{
  "reason": "Violation of terms"
}
```

### Response

```json
{
  "success": true,
  "message": "User account suspended successfully"
}
```

---

## Activate User

```http
POST /admin/users/{user_id}/activate
```

### Response

```json
{
  "success": true,
  "message": "User account activated successfully"
}
```

---

## List Doctors

```http
GET /admin/doctors
```

### Query Parameters

```text
status (pending|approved|rejected|suspended)
page
limit
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "doctor_id",
      "user_id": "user_id",
      "email": "doctor@example.com",
      "full_name": "Doctor Name",
      "specialization": "Cardiology",
      "verification_status": "pending",
      "created_at": "2026-06-24T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

---

## Approve Doctor

```http
POST /admin/doctors/{doctor_id}/approve
```

### Response

```json
{
  "success": true,
  "message": "Doctor verification approved successfully"
}
```

---

## Reject Doctor

```http
POST /admin/doctors/{doctor_id}/reject
```

### Request

```json
{
  "reason": "Invalid medical license details"
}
```

### Response

```json
{
  "success": true,
  "message": "Doctor verification rejected successfully"
}
```

---

## Suspend Doctor

```http
POST /admin/doctors/{doctor_id}/suspend
```

### Request

```json
{
  "reason": "Patient complaints"
}
```

### Response

```json
{
  "success": true,
  "message": "Doctor profile suspended successfully"
}
```

---

## Reactivate Doctor

```http
POST /admin/doctors/{doctor_id}/reactivate
```

### Response

```json
{
  "success": true,
  "message": "Doctor profile reactivated successfully"
}
```

---

## Platform Analytics

```http
GET /admin/analytics
```

### Response

```json
{
  "success": true,
  "data": {
    "user_metrics": {
      "total_users": 1000,
      "active_users": 850,
      "growth_trends": [
        {
          "date": "2026-06",
          "count": 1000
        }
      ]
    },
    "doctor_metrics": {
      "total_doctors": 150,
      "verification_metrics": {
        "pending": 10,
        "approved": 130,
        "rejected": 5,
        "suspended": 5
      },
      "activity_metrics": {
        "active_slots": 500,
        "booked_slots": 350
      }
    },
    "appointment_metrics": {
      "pending": 20,
      "approved": 50,
      "completed": 400,
      "cancelled": 30
    },
    "revenue_metrics": {
      "doctor_earnings": 170000,
      "platform_revenue": 30000,
      "revenue_trends": [
        {
          "date": "2026-06",
          "earnings": 170000,
          "platform": 30000
        }
      ]
    },
    "healthcare_metrics": {
      "reports_analyzed": 450,
      "consultations_completed": 400,
      "prescriptions_generated": 380
    }
  }
}
```

---

## Audit Logs

```http
GET /admin/audit-logs
```

### Query Parameters

```text
admin_id
action
page
limit
```

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "log_id",
      "admin_id": "admin_id",
      "admin_name": "Admin Name",
      "action": "suspend_user",
      "target_id": "user_id",
      "target_type": "user",
      "details": {
        "reason": "Terms violation"
      },
      "ip_address": "127.0.0.1",
      "created_at": "2026-06-24T12:05:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 1,
    "pages": 1
  }
}
```

---

# 13. Health API

## System Health

```http
GET /health
```

### Response

```json
{
  "status": "healthy",
  "mongodb": "connected",
  "qdrant": "connected"
}
```

---

# 14. Authentication Rules

Protected endpoints require:

```http
Authorization: Bearer <token>
```

---

# 15. Role Permissions

## Patient

```text
Reports
Reminders
Appointments
Chat
Doctors
```

---

## Doctor

```text
Patients
Appointments
Availability
Earnings
```

---

## Admin

```text
Users
Doctors
Payments
Analytics
Audit Logs
```

---

# 16. Error Codes

## Validation Error

```http
400 Bad Request
```

---

## Unauthorized

```http
401 Unauthorized
```

---

## Forbidden

```http
403 Forbidden
```

---

## Not Found

```http
404 Not Found
```

---

## Conflict

```http
409 Conflict
```

---

## Internal Error

```http
500 Internal Server Error
```

---

# 17. Definition of Done

API contract is considered complete when:

* Frontend and backend use identical request schemas
* Response formats are standardized
* Authentication requirements are defined
* Error handling is standardized
* Role permissions are documented
* All MVP endpoints are covered

```
```
