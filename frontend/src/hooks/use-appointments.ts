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

export function useDoctorAppointments() {
  return useQuery({
    queryKey: ['appointments', 'doctor'],
    queryFn: async () => {
      const response = await appointmentsService.getDoctorAppointments()
      if (response.success && response.data) {
        return response.data.appointments
      }
      throw new Error(response.message || 'Failed to fetch doctor appointments')
    },
    staleTime: 15_000,
  })
}

export function useApproveAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (appointmentId: string) => {
      const response = await appointmentsService.approveAppointment(appointmentId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to approve appointment')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
    },
  })
}

export function useRejectAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ appointmentId, rejectionReason }: { appointmentId: string; rejectionReason: string }) => {
      const response = await appointmentsService.rejectAppointment(appointmentId, rejectionReason)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to reject appointment')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
    },
  })
}

export function useStartConsultation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (appointmentId: string) => {
      const response = await appointmentsService.startConsultation(appointmentId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to start consultation')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['consultations'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
    },
  })
}

export function useCompleteConsultation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ appointmentId, payload }: { appointmentId: string; payload: any }) => {
      const response = await appointmentsService.completeConsultation(appointmentId, payload)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to complete consultation')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      queryClient.invalidateQueries({ queryKey: ['consultations'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['patient', 'dashboard'] })
    },
  })
}

export function useDoctorConsultations() {
  return useQuery({
    queryKey: ['consultations', 'doctor'],
    queryFn: async () => {
      const response = await appointmentsService.getDoctorConsultations()
      if (response.success && response.data) {
        return response.data.consultations
      }
      throw new Error(response.message || 'Failed to fetch consultations')
    },
    staleTime: 15_000,
  })
}
