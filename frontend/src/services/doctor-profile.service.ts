import apiClient from '@/lib/axios'
import { ApiResponse, DoctorProfile, DoctorDocument } from '@/types'

export interface DoctorProfileManagementResponseData {
  profile: DoctorProfile
  documents: DoctorDocument[]
}

export interface DoctorProfileManagementUpdateRequest {
  bio?: string
  consultation_fee?: number
  languages?: string[]
  education?: string
  experience_years?: number
}

export const doctorProfileService = {
  getDoctorProfile: async (): Promise<ApiResponse<DoctorProfileManagementResponseData>> => {
    const response = await apiClient.get<ApiResponse<DoctorProfileManagementResponseData>>('/doctor/profile')
    return response.data
  },
  updateDoctorProfile: async (
    profile: DoctorProfileManagementUpdateRequest
  ): Promise<ApiResponse<DoctorProfileManagementResponseData>> => {
    const response = await apiClient.put<ApiResponse<DoctorProfileManagementResponseData>>('/doctor/profile', profile)
    return response.data
  },
}
