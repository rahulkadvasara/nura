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
  profile_status: 'pending' | 'verified' | 'rejected' | 'suspended'
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
  profile_status: 'pending' | 'verified' | 'rejected' | 'suspended'
  rejection_reason?: string
  average_rating: number
  total_reviews: number
  created_at: string
  updated_at: string
}

export interface DoctorApplicationData {
  application_status: string
  profile_status: 'pending' | 'verified' | 'rejected' | 'suspended'
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
  profile_status: 'pending' | 'verified' | 'rejected' | 'suspended'
  created_at: string
  is_active?: boolean
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

export interface AgentLog {
  id: string
  agent_name: string
  workflow_id: string
  session_id?: string
  patient_id?: string
  user_id?: string
  input_payload: Record<string, any>
  output_payload: Record<string, any>
  status: 'started' | 'completed' | 'failed'
  latency_ms: number
  token_usage: Record<string, number>
  error_message?: string
  langgraph_thread_id?: string
  langgraph_checkpoint_id?: string
  langfuse_trace_id?: string
  langfuse_parent_observation_id?: string
  orchestrator_node?: string
  evaluation_metrics?: Record<string, any>
  research_metadata?: Record<string, any>
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

export interface DailyGrowthItem {
  date: string
  count: number
}

export interface DailyRevenueItem {
  date: string
  amount: number
}

export interface AdminAnalyticsData {
  users: {
    total_users: number
    active_users: number
    inactive_users: number
    patients_count: number
    doctors_count: number
    admins_count: number
    users_last_7_days: DailyGrowthItem[]
    users_last_30_days: DailyGrowthItem[]
  }
  doctors: {
    total_doctors: number
    verified_doctors: number
    pending_doctors: number
    rejected_doctors: number
    suspended_doctors: number
    doctors_with_availability: number
    active_doctors: number
  }
  appointments: {
    total_appointments: number
    pending_appointments: number
    approved_appointments: number
    completed_appointments: number
    cancelled_appointments: number
    rejected_appointments: number
    appointments_last_7_days: DailyGrowthItem[]
    appointments_last_30_days: DailyGrowthItem[]
  }
  revenue: {
    total_revenue: number
    doctor_earnings: number
    platform_revenue: number
    revenue_last_7_days: DailyRevenueItem[]
    revenue_last_30_days: DailyRevenueItem[]
  }
  healthcare: {
    reports_uploaded: number
    consultations_completed: number
    prescriptions_created: number
    reminders_created: number
    reports_last_30_days: DailyGrowthItem[]
    consultations_last_30_days: DailyGrowthItem[]
  }
}

// Doctor Patient Management Types
export interface Report {
  id: string
  patient_id: string
  filename: string
  file_url: string
  risk_level?: string
  processing_status: string
  summary?: string
  created_at: string
  updated_at: string
}

export interface HealthInsight {
  id: string
  patient_id: string
  title: string
  summary: string
  recommendations: string[]
  severity: 'low' | 'medium' | 'high'
  created_at: string
  updated_at: string
}

export interface Reminder {
  id: string
  patient_id: string
  title: string
  description?: string
  time: string
  frequency: string
  status: string
  created_at: string
  updated_at: string
}

export interface ChatSession {
  id: string
  patient_id: string
  doctor_id: string
  session_type: string
  status: string
  last_message_at: string
  created_at: string
  updated_at: string
}

export interface DoctorPatientSummary {
  patient_id: string
  name: string
  age?: number
  gender?: string
  profile_picture?: string
  latest_appointment?: Appointment
  latest_consultation?: Consultation
  total_appointments: number
  total_consultations: number
  total_reports: number
  health_risk_level?: string
}

export interface DoctorPatientListResponse {
  patients: DoctorPatientSummary[]
  total: number
}

export interface DoctorPatientDetail {
  profile: User
  appointment_history: Appointment[]
  consultation_history: Consultation[]
  reports: Report[]
  prescriptions: Prescription[]
  health_insights: HealthInsight[]
  current_reminders: Reminder[]
  latest_chat_session?: ChatSession
}

// Doctor Earnings Dashboard Types (Sprint 8)
export interface MonthlyEarningsItem {
  month: string
  amount: number
}

export interface RevenueTrendItem {
  date: string
  amount: number
}

export interface DoctorWalletResponse {
  id: string
  doctor_id: string
  total_earned: number
  total_withdrawn: number
  available_balance: number
  pending_balance: number
  last_payout_at?: string
  created_at: string
  updated_at: string
}

export interface DoctorEarningsResponse {
  available_balance: number
  pending_balance: number
  lifetime_earnings: number
  platform_revenue_share: number
  doctor_revenue_share: number
  total_consultations: number
  total_completed_consultations: number
  average_consultation_fee: number
  monthly_earnings_summary: MonthlyEarningsItem[]
  recent_transactions: Appointment[] // Or we can use more detailed representation if needed, but since it is PaymentResponse in backend, let's look at what fields PaymentResponse has. Since we also have DoctorTransactionItem, we will use that for listing. Recent transactions in DoctorEarningsResponse is actually PaymentResponse.
  revenue_trend: RevenueTrendItem[]
}

export interface DoctorWalletDetailsResponse {
  wallet_details: DoctorWalletResponse
  pending_amount: number
  available_amount: number
  lifetime_earnings: number
  total_withdrawn: number
}

export interface DoctorTransactionItem {
  id: string
  appointment_id: string
  patient_id: string
  patient_name: string
  consultation_fee: number
  doctor_share: number
  platform_share: number
  status: string
  created_at: string
}

export interface DoctorTransactionsResponse {
  transactions: DoctorTransactionItem[]
  total: number
}




