import apiClient from '@/lib/axios'
import { ApiResponse, DoctorApplicationRequest, DoctorApplicationUpdateRequest, DoctorApplicationData } from '@/types'

export const doctorApplicationService = {
  applyAsDoctor: async (data: DoctorApplicationRequest): Promise<ApiResponse<DoctorApplicationData>> => {
    const response = await apiClient.post<ApiResponse<DoctorApplicationData>>('/doctor/apply', data)
    return response.data
  },
  getDoctorApplication: async (): Promise<ApiResponse<DoctorApplicationData>> => {
    const response = await apiClient.get<ApiResponse<DoctorApplicationData>>('/doctor/application')
    return response.data
  },
  updateDoctorApplication: async (data: DoctorApplicationUpdateRequest): Promise<ApiResponse<DoctorApplicationData>> => {
    const response = await apiClient.put<ApiResponse<DoctorApplicationData>>('/doctor/application', data)
    return response.data
  },
}
