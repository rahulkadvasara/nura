"""
Nura - Application Constants
"""

# User Roles
USER_ROLES = {
    "PATIENT": "patient",
    "DOCTOR": "doctor",
    "ADMIN": "admin"
}

# Appointment Statuses
APPOINTMENT_STATUS = {
    "PENDING": "pending",
    "APPROVED": "approved", 
    "REJECTED": "rejected",
    "COMPLETED": "completed",
    "CANCELLED": "cancelled"
}

# Payment Statuses
PAYMENT_STATUS = {
    "PENDING": "pending",
    "HELD": "held",
    "APPROVED": "approved",
    "COMPLETED": "completed",
    "REFUNDED": "refunded",
    "FAILED": "failed"
}

# Report Risk Levels
RISK_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium", 
    "HIGH": "high"
}

# Drug Interaction Risk Levels
DRUG_RISK_LEVELS = {
    "LOW": "low",
    "MEDIUM": "medium",
    "HIGH": "high",
    "EMERGENCY": "emergency"
}

# Reminder Repeat Types
REMINDER_TYPES = {
    "DAILY": "daily",
    "WEEKLY": "weekly", 
    "MONTHLY": "monthly"
}

# Notification Types
NOTIFICATION_TYPES = {
    "APPOINTMENT": "appointment",
    "REMINDER": "reminder",
    "REPORT": "report",
    "PAYMENT": "payment",
    "SYSTEM": "system"
}

# Doctor Verification Statuses
VERIFICATION_STATUS = {
    "PENDING": "pending",
    "APPROVED": "approved",
    "REJECTED": "rejected"
}

# Auth Providers
AUTH_PROVIDERS = {
    "LOCAL": "local",
    "GOOGLE": "google"
}

# AI Agent Names
AI_AGENTS = {
    "ROUTER": "RouterAgent",
    "RETRIEVAL": "RetrievalAgent",
    "SYMPTOM": "SymptomAgent", 
    "MEDICAL_KNOWLEDGE": "MedicalKnowledgeAgent",
    "REPORT_ANALYSIS": "ReportAnalysisAgent",
    "DRUG_INTERACTION": "DrugInteractionAgent",
    "DOCTOR_RECOMMENDATION": "DoctorRecommendationAgent",
    "REMINDER": "ReminderAgent",
    "APPOINTMENT": "AppointmentAgent",
    "MEMORY": "MemoryAgent"
}

# Qdrant Collections
QDRANT_COLLECTIONS = {
    "PATIENT_REPORTS": "patient_reports",
    "CHAT_MEMORY": "chat_memory",
    "MEDICAL_KNOWLEDGE": "medical_knowledge",
    "DRUG_KNOWLEDGE": "drug_knowledge",
    "DOCTOR_KNOWLEDGE": "doctor_knowledge"
}

# Revenue Split Configuration
REVENUE_SPLIT = {
    "DOCTOR_SHARE_PERCENT": 85,
    "PLATFORM_SHARE_PERCENT": 15
}