import apiClient from '@/lib/axios'
import { ApiResponse, Appointment } from '@/types'

export interface PaymentOrderResponse {
  razorpay_order_id: string
  amount: number
  currency: string
  razorpay_key_id: string
  appointment: Appointment
}

export interface PaymentVerifyRequest {
  razorpay_payment_id: string
  razorpay_order_id: string
  razorpay_signature: string
}

export interface PaymentVerifyResponse {
  payment: {
    id: string
    appointment_id: string
    patient_id: string
    doctor_id: string
    amount: number
    currency: string
    razorpay_order_id: string
    razorpay_payment_id?: string
    payment_status: string
    verified_at?: string
    created_at: string
  }
  appointment: Appointment
  wallet_update_summary: {
    wallet_id: string
    doctor_id: string
    old_balance: number
    new_balance: number
    increment: number
  }
  revenue_split_summary: {
    doctor_id: string
    amount: number
    doctor_share: number
    platform_share: number
  }
}

export const paymentService = {
  createOrder: async (appointmentId: string): Promise<ApiResponse<PaymentOrderResponse>> => {
    const response = await apiClient.post<ApiResponse<PaymentOrderResponse>>('/payments/order', {
      appointment_id: appointmentId,
    })
    return response.data
  },

  verifyPayment: async (payload: PaymentVerifyRequest): Promise<ApiResponse<PaymentVerifyResponse>> => {
    const response = await apiClient.post<ApiResponse<PaymentVerifyResponse>>('/payments/verify', payload)
    return response.data
  },
}

