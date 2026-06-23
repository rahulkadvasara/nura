import apiClient from '@/lib/axios'
import { ApiResponse, Appointment, PatientAppointmentHistoryItem, AppointmentCreateRequest } from '@/types'

export const appointmentsService = {
  createAppointment: async (payload: AppointmentCreateRequest): Promise<ApiResponse<Appointment>> => {
    const response = await apiClient.post<ApiResponse<Appointment>>('/appointments', payload)
    return response.data
  },

  getMyAppointments: async (): Promise<ApiResponse<{ appointments: PatientAppointmentHistoryItem[] }>> => {
    const response = await apiClient.get<ApiResponse<{ appointments: PatientAppointmentHistoryItem[] }>>('/appointments/my')
    return response.data
  },

  getAppointmentDetails: async (appointmentId: string): Promise<ApiResponse<Appointment>> => {
    const response = await apiClient.get<ApiResponse<Appointment>>(`/appointments/${appointmentId}`)
    return response.data
  },

  cancelAppointment: async (appointmentId: string): Promise<ApiResponse<void>> => {
    const response = await apiClient.delete<ApiResponse<void>>(`/appointments/${appointmentId}`)
    return response.data
  },
}
