import { useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentService, PaymentVerifyRequest } from '@/services/payment.service'

export function useCreatePaymentOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (appointmentId: string) => {
      const response = await paymentService.createOrder(appointmentId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to initialize payment')
    },
    onSuccess: () => {
      // Invalidate current appointments list so payment status / status is updated
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
    },
  })
}

export function useVerifyPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: PaymentVerifyRequest) => {
      const response = await paymentService.verifyPayment(payload)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to verify payment')
    },
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'earnings'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'wallet'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'transactions'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'payment-history'] })
    },
  })
}

export function useFailPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ paymentId, errorDetails }: { paymentId: string; errorDetails?: any }) => {
      const response = await paymentService.failPayment(paymentId, errorDetails)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to record payment failure')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'payment-history'] })
    },
  })
}

export function useCancelPayment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (paymentId: string) => {
      const response = await paymentService.cancelPayment(paymentId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to record payment cancellation')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'payment-history'] })
    },
  })
}


