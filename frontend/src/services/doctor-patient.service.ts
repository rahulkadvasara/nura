import apiClient from '@/lib/axios'
import { ApiResponse, DoctorPatientListResponse, DoctorPatientDetail } from '@/types'

export const doctorPatientService = {
  getPatients: async (params?: {
    search?: string
    sort_by?: string
    limit?: number
    skip?: number
  }): Promise<ApiResponse<DoctorPatientListResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorPatientListResponse>>('/doctor/patients', { params })
    return response.data
  },

  getPatientDetail: async (patientId: string): Promise<ApiResponse<DoctorPatientDetail>> => {
    const response = await apiClient.get<ApiResponse<DoctorPatientDetail>>(`/doctor/patients/${patientId}`)
    return response.data
  }
}
