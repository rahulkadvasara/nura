import { useQuery } from '@tanstack/react-query'
import { paymentAdminService } from '@/services/payment-admin.service'

export function usePaymentHistory(params?: {
  search?: string
  status_filter?: string
  doctor_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  skip?: number
}) {
  return useQuery({
    queryKey: ['patient', 'payment-history', params],
    queryFn: async () => {
      const response = await paymentAdminService.getPatientHistory(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch patient payment history')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useAdminPayments(params?: {
  search?: string
  status_filter?: string
  doctor_id?: string
  patient_id?: string
  start_date?: string
  end_date?: string
  limit?: number
  skip?: number
}) {
  return useQuery({
    queryKey: ['admin', 'payments', params],
    queryFn: async () => {
      const response = await paymentAdminService.getAdminPayments(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch platform payments')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useRevenueSummary() {
  return useQuery({
    queryKey: ['admin', 'revenue-summary'],
    queryFn: async () => {
      const response = await paymentAdminService.getAdminPaymentsSummary()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch platform revenue summary')
    },
  })
}

export function useAdminPaymentDetail(paymentId: string | null) {
  return useQuery({
    queryKey: ['admin', 'payment-detail', paymentId],
    queryFn: async () => {
      if (!paymentId) return null
      const response = await paymentAdminService.getAdminPaymentDetail(paymentId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch payment details')
    },
    enabled: !!paymentId,
  })
}
