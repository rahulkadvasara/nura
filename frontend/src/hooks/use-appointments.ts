import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { appointmentsService } from '@/services/appointments.service'
import { AppointmentCreateRequest } from '@/types'

export function useAppointments() {
  return useQuery({
    queryKey: ['appointments', 'my'],
    queryFn: async () => {
      const response = await appointmentsService.getMyAppointments()
      if (response.success && response.data) {
        return response.data.appointments
      }
      throw new Error(response.message || 'Failed to fetch appointments')
    },
    staleTime: 15_000, // cache for 15 seconds
  })
}

export function useCreateAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (payload: AppointmentCreateRequest) => {
      const response = await appointmentsService.createAppointment(payload)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to create appointment request')
    },
    onSuccess: () => {
      // Invalidate current appointments list
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['doctors', 'availability'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
    },
  })
}

export function useCancelAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (appointmentId: string) => {
      const response = await appointmentsService.cancelAppointment(appointmentId)
      if (response.success) {
        return response.data
      }
      throw new Error(response.message || 'Failed to cancel appointment')
    },
    onSuccess: () => {
      // Invalidate current appointments list
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['doctors', 'availability'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
    },
  })
}
