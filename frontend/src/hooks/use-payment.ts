import { useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentService } from '@/services/payment.service'

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
