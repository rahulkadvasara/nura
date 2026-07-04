import apiClient from '@/lib/axios'
import { ApiResponse } from '@/types'

export interface PatientPaymentHistoryItem {
  payment_id: string
  appointment: {
    id: string
    slot_date: string
    slot_time: string
    status: string
    reason?: string
  }
  doctor: {
    id: string
    full_name: string
    specialization: string
    email: string
  }
  amount: number
  status: string
  created_date: string
  paid_date?: string
  receipt_information?: {
    razorpay_order_id?: string
    razorpay_payment_id?: string
    payment_method?: string
    transaction_reference?: string
    doctor_share?: number
    platform_fee?: number
  }
}

export interface PatientPaymentHistoryResponse {
  payments: PatientPaymentHistoryItem[]
  total: number
}

export interface AdminPaymentListItem {
  payment_id: string
  appointment_id: string
  patient: {
    id: string
    full_name: string
    email: string
  }
  doctor: {
    id: string
    full_name: string
    email: string
    specialization: string
  }
  amount: number
  doctor_share: number
  platform_share: number
  payment_status: string
  created_at: string
  verified_at?: string
}

export interface AdminPaymentListResponse {
  payments: AdminPaymentListItem[]
  total: number
}

export interface MonthlyRevenueItem {
  month: string
  amount: number
  doctor_share: number
  platform_share: number
}

export interface DailyRevenueItem {
  date: string
  amount: number
  doctor_share: number
  platform_share: number
}

export interface AdminRevenueSummaryResponse {
  total_revenue: number
  doctor_payouts: number
  platform_earnings: number
  successful_payments: number
  failed_payments: number
  pending_payments: number
  average_consultation_fee: number
  total_transactions: number
  monthly_revenue: MonthlyRevenueItem[]
  daily_revenue: DailyRevenueItem[]
  pending_payouts: number
  refunded_payments: number
  refunded_revenue: number
  failed_revenue: number
}


export interface AdminPaymentDetail {
  payment_id: string
  appointment_id: string
  appointment: {
    id: string
    slot_date: string
    slot_time: string
    status: string
    reason?: string
    consultation_fee: number
  }
  patient: {
    id: string
    full_name: string
    email: string
  }
  doctor: {
    id: string
    full_name: string
    email: string
    specialization: string
  }
  amount: number
  doctor_share: number
  platform_share: number
  payment_status: string
  razorpay_order_id?: string
  razorpay_payment_id?: string
  gateway_response?: Record<string, any>
  created_at: string
  verified_at?: string
}

export const paymentAdminService = {
  getPatientHistory: async (params?: {
    search?: string
    status_filter?: string
    doctor_id?: string
    start_date?: string
    end_date?: string
    limit?: number
    skip?: number
  }): Promise<ApiResponse<PatientPaymentHistoryResponse>> => {
    const response = await apiClient.get<ApiResponse<PatientPaymentHistoryResponse>>('/payments/history', {
      params,
    })
    return response.data
  },

  getAdminPayments: async (params?: {
    search?: string
    status_filter?: string
    doctor_id?: string
    patient_id?: string
    start_date?: string
    end_date?: string
    limit?: number
    skip?: number
  }): Promise<ApiResponse<AdminPaymentListResponse>> => {
    const response = await apiClient.get<ApiResponse<AdminPaymentListResponse>>('/admin/payments', {
      params,
    })
    return response.data
  },

  getAdminPaymentsSummary: async (): Promise<ApiResponse<AdminRevenueSummaryResponse>> => {
    const response = await apiClient.get<ApiResponse<AdminRevenueSummaryResponse>>('/admin/payments/summary')
    return response.data
  },

  getAdminPaymentDetail: async (paymentId: string): Promise<ApiResponse<AdminPaymentDetail>> => {
    const response = await apiClient.get<ApiResponse<AdminPaymentDetail>>(`/admin/payments/${paymentId}`)
    return response.data
  },
}
