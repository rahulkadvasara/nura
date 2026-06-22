import apiClient from '@/lib/axios'
import { ApiResponse, DoctorAvailability } from '@/types'

export interface DoctorDiscoveryResponseData {
  id: string
  user_id: string
  name: string
  specialization: string
  qualifications: string[]
  experience_years: number
  consultation_fee: number
  bio?: string
  languages: string[]
  hospital?: string
  education?: string
  profile_picture?: string
  average_rating: number
  total_reviews: number
}

export interface DoctorsListResponse {
  doctors: DoctorDiscoveryResponseData[]
}

export interface DoctorAvailabilityListResponse {
  slots: DoctorAvailability[]
}

export const doctorDiscoveryService = {
  getDoctors: async (params?: {
    search?: string
    specialization?: string
    min_experience?: number
  }): Promise<ApiResponse<DoctorsListResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorsListResponse>>('/doctors', {
      params,
    })
    return response.data
  },

  getDoctorDetails: async (doctorId: string): Promise<ApiResponse<DoctorDiscoveryResponseData>> => {
    const response = await apiClient.get<ApiResponse<DoctorDiscoveryResponseData>>(`/doctors/${doctorId}`)
    return response.data
  },

  getDoctorAvailability: async (doctorId: string): Promise<ApiResponse<DoctorAvailabilityListResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorAvailabilityListResponse>>(`/doctors/${doctorId}/availability`)
    return response.data
  },
}
