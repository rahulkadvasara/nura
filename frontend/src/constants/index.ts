// Application Constants

export const APP_CONFIG = {
  NAME: process.env.NEXT_PUBLIC_APP_NAME || 'Nura',
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
} as const

export const USER_ROLES = {
  PATIENT: 'patient',
  DOCTOR: 'doctor',
  ADMIN: 'admin',
} as const

export const APPOINTMENT_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected', 
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const

export const RISK_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const

export const REMINDER_TYPES = {
  DAILY: 'daily',
  WEEKLY: 'weekly',
  MONTHLY: 'monthly',
} as const