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
  last_login_at?: string
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

export interface PatientDashboardConsultation {
  id: string
  doctor_name: string
  specialization: string
  date: string
  diagnosis: string
}

export interface PatientDashboardPrescription {
  id: string
  doctor_name: string
  date: string
  medications_count: number
}

export interface PatientDashboardData {
  upcoming_appointments_count: number
  active_reminders_count: number
  reports_count: number
  unread_notifications_count: number
  recent_health_insights: RecentHealthInsight[]
  recent_consultation?: PatientDashboardConsultation
  recent_prescription?: PatientDashboardPrescription
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
  prescriptions_written_count: number
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

// Doctor Application Types
export interface DoctorApplicationRequest {
  specialization: string
  experience_years: number
  consultation_fee: number
  bio?: string
  education: string
  languages: string[]
  hospital?: string
  license_number?: string
  degree_certificate_url: string
  medical_license_url: string
  identity_proof_url: string
}

export interface DoctorApplicationUpdateRequest {
  specialization?: string
  experience_years?: number
  consultation_fee?: number
  bio?: string
  education?: string
  languages?: string[]
  hospital?: string
  license_number?: string
  degree_certificate_url?: string
  medical_license_url?: string
  identity_proof_url?: string
}

export interface DoctorDocument {
  id: string
  doctor_id: string
  document_type: 'license' | 'degree' | 'certificate' | 'id_proof' | 'other'
  document_url: string
  verification_status: 'pending' | 'approved' | 'rejected'
  uploaded_at: string
  verified_at?: string
  verified_by?: string
}

export interface DoctorProfile {
  id: string
  user_id: string
  specialization: string
  experience_years: number
  consultation_fee: number
  bio?: string
  education?: string
  languages: string[]
  hospital?: string
  license_number?: string
  profile_status: 'pending' | 'verified' | 'rejected'
  rejection_reason?: string
  average_rating: number
  total_reviews: number
  created_at: string
  updated_at: string
}

export interface DoctorApplicationData {
  application_status: string
  profile_status: 'pending' | 'verified' | 'rejected'
  profile: DoctorProfile
  documents: DoctorDocument[]
}

export interface AdminDoctorListResponse {
  id: string
  user_id: string
  full_name: string
  email: string
  specialization: string
  experience_years: number
  consultation_fee: number
  hospital?: string
  license_number?: string
  education?: string
  profile_status: 'pending' | 'verified' | 'rejected'
  created_at: string
}

export interface DoctorVerificationResponse {
  profile: DoctorProfile
  user: {
    id: string
    role: 'patient' | 'doctor' | 'admin'
    email: string
    full_name: string
    email_verified: boolean
  }
  documents: DoctorDocument[]
}

// Doctor Availability Types
export interface DoctorAvailability {
  id: string
  doctor_id: string
  date: string
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
  start_time: string
  end_time: string
  slot_duration: number
  is_available: boolean
  active: boolean
  created_at: string
  updated_at: string
}

export interface DoctorAvailabilityCreateRequest {
  date: string
  day_of_week?: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
  start_time: string
  end_time: string
  slot_duration?: number
  is_available?: boolean
  active?: boolean
}

export interface DoctorAvailabilityUpdateRequest {
  date?: string
  day_of_week?: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
  start_time?: string
  end_time?: string
  slot_duration?: number
  is_available?: boolean
  active?: boolean
}

// Appointment Types
export interface Appointment {
  id: string
  patient_id: string
  doctor_id: string
  availability_id?: string
  slot_date: string
  slot_time: string
  duration_minutes: number
  consultation_fee: number
  status: 'pending' | 'approved' | 'in_progress' | 'rejected' | 'cancelled' | 'completed'
  payment_status: 'pending' | 'held' | 'approved' | 'completed' | 'refunded' | 'failed'
  reason?: string
  notes?: string
  rejection_reason?: string
  consultation_started_at?: string
  consultation_completed_at?: string
  created_at: string
  updated_at: string
}

export interface PatientAppointmentHistoryItem {
  id: string
  doctor_id: string
  doctor_name: string
  specialization: string
  appointment_date: string
  appointment_time: string
  status: 'pending' | 'approved' | 'in_progress' | 'rejected' | 'cancelled' | 'completed'
  reason?: string
  rejection_reason?: string
  created_at: string
}

export interface DoctorAppointmentItem {
  id: string
  patient_id: string
  patient_name: string
  appointment_date: string
  appointment_time: string
  reason: string
  status: 'pending' | 'approved' | 'in_progress' | 'rejected' | 'cancelled' | 'completed'
  rejection_reason?: string
  created_at: string
}

export interface AppointmentCreateRequest {
  doctor_id: string
  availability_id: string
  reason: string
}

export interface ConsultationCompleteRequest {
  diagnosis: string
  notes: string
  follow_up_required: boolean
  follow_up_date?: string
}

export interface Consultation {
  id: string
  appointment_id: string
  patient_id: string
  doctor_id: string
  consultation_notes: string
  diagnosis: string
  recommendations?: string
  follow_up_required: boolean
  follow_up_date?: string
  created_at: string
  updated_at: string
}

export interface DoctorConsultationItem {
  id: string
  appointment_id: string
  patient_id: string
  patient_name: string
  diagnosis: string
  consultation_notes: string
  follow_up_required: boolean
  follow_up_date?: string
  created_at: string
}

// Prescription Types
export interface Medication {
  drug_name: string
  dosage: string
  frequency: string
  duration: string
  instructions?: string
}

export interface Prescription {
  id: string
  consultation_id: string
  patient_id: string
  doctor_id: string
  medications: Medication[]
  dosage_instructions?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface PrescriptionCreateRequest {
  medications: Medication[]
  dosage_instructions?: string
  notes?: string
}

export interface PrescriptionUpdateRequest {
  medications?: Medication[]
  dosage_instructions?: string
  notes?: string
}

export interface PatientConsultationItem {
  id: string
  appointment_id: string
  patient_id: string
  doctor_id: string
  doctor_name: string
  doctor_specialization: string
  appointment_date: string
  appointment_time: string
  diagnosis: string
  consultation_notes: string
  follow_up_required: boolean
  follow_up_date?: string
  prescription_status: 'Prescribed' | 'No Prescription'
  prescription_id?: string
  created_at: string
  updated_at: string
}

export interface PatientPrescription {
  id: string
  consultation_id: string
  patient_id: string
  doctor_id: string
  doctor_name: string
  doctor_specialization: string
  diagnosis: string
  medications: Medication[]
  dosage_instructions?: string
  notes?: string
  created_at: string
  updated_at: string
}

// Admin Management Types
export interface AdminCreateRequest {
  full_name: string
  email: string
}

export interface AdminCreateResponse {
  id: string
  full_name: string
  email: string
  role: string
  is_active: boolean
  email_verified: boolean
  created_at: string
  temporary_password: string
}

export interface AuditLog {
  id: string
  user_id?: string
  action: string
  resource_type: string
  resource_id?: string
  old_value?: any
  new_value?: any
  ip_address?: string
  user_agent?: string
  created_at: string
}

export interface AdminDetailResponse {
  profile: User
  account_status: {
    is_active: boolean
    email_verified: boolean
  }
  audit_summary: AuditLog[]
}

export interface AdminSession {
  id: string
  created_at: string
  expires_at: string
  revoked: boolean
  last_activity: string
}


