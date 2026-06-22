import apiClient from '@/lib/axios'
import { ApiResponse, DoctorAvailability, DoctorAvailabilityCreateRequest, DoctorAvailabilityUpdateRequest } from '@/types'

export const doctorAvailabilityService = {
  getAvailability: async (): Promise<ApiResponse<DoctorAvailability[]>> => {
    const response = await apiClient.get<ApiResponse<{ availability: DoctorAvailability[] }>>('/doctor/availability')
    return {
      success: response.data.success,
      message: response.data.message,
      data: response.data.data?.availability || [],
      errors: response.data.errors
    }
  },
  createAvailabilitySlot: async (slot: DoctorAvailabilityCreateRequest): Promise<ApiResponse<DoctorAvailability>> => {
    const response = await apiClient.post<ApiResponse<DoctorAvailability>>('/doctor/availability', slot)
    return response.data
  },
  updateAvailabilitySlot: async (id: string, slot: DoctorAvailabilityUpdateRequest): Promise<ApiResponse<DoctorAvailability>> => {
    const response = await apiClient.put<ApiResponse<DoctorAvailability>>(`/doctor/availability/${id}`, slot)
    return response.data
  },
  deleteAvailabilitySlot: async (id: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.delete<ApiResponse<null>>(`/doctor/availability/${id}`)
    return response.data
  },
}
