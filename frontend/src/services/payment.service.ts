import apiClient from '@/lib/axios'
import { ApiResponse, Appointment } from '@/types'

export interface PaymentOrderResponse {
  razorpay_order_id: string
  amount: number
  currency: string
  razorpay_key_id: string
  appointment: Appointment
}

export const paymentService = {
  createOrder: async (appointmentId: string): Promise<ApiResponse<PaymentOrderResponse>> => {
    const response = await apiClient.post<ApiResponse<PaymentOrderResponse>>('/payments/order', {
      appointment_id: appointmentId,
    })
    return response.data
  },
}
