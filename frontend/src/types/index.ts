// Common Types

export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  errors?: string[]
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number
    limit: number
    total: number
    pages: number
  }
}

// User Types
export interface User {
  id: string
  role: 'patient' | 'doctor' | 'admin'
  email: string
  full_name: string
  phone?: string
  profile_picture?: string
  auth_provider: 'local' | 'google'
  email_verified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

// Health Types
export interface HealthStatus {
  status: string
  app: string
  environment: string
  mongodb: string
  qdrant: string
}

// Dashboard Types
export interface RecentHealthInsight {
  id: string
  title: string
  severity: 'low' | 'medium' | 'high' | null
  created_at: string
}

export interface PatientDashboardData {
  upcoming_appointments_count: number
  active_reminders_count: number
  reports_count: number
  unread_notifications_count: number
  recent_health_insights: RecentHealthInsight[]
}

export interface DoctorDashboardData {
  todays_appointments_count: number
  upcoming_appointments_count: number
  total_patients_count: number
  pending_approvals_count: number
  wallet_balance: number
  total_earnings: number
  pending_balance: number
  profile_status: 'pending' | 'verified' | 'rejected'
  document_status: 'pending' | 'approved' | 'rejected'
}

export interface AdminDashboardData {
  total_users_count: number
  total_patients_count: number
  total_doctors_count: number
  pending_doctor_verifications_count: number
  total_appointments_count: number
  total_revenue: number
  platform_earnings: number
  active_consultations_count: number
  reports_count: number
  reminders_count: number
  active_chats_count: number
  verified_doctors_count: number
}
