import apiClient from '@/lib/axios'
import { ApiResponse, AdminDoctorListResponse, DoctorVerificationResponse } from '@/types'

export const adminDoctorService = {
  getPendingDoctors: async (): Promise<ApiResponse<AdminDoctorListResponse[]>> => {
    const response = await apiClient.get<ApiResponse<{ doctors: AdminDoctorListResponse[] }>>('/admin/doctors/pending')
    return {
      success: response.data.success,
      message: response.data.message,
      data: response.data.data?.doctors || [],
      errors: response.data.errors
    }
  },
  getDoctorDetail: async (profileId: string): Promise<ApiResponse<DoctorVerificationResponse>> => {
    const response = await apiClient.get<ApiResponse<DoctorVerificationResponse>>(`/admin/doctors/${profileId}`)
    return response.data
  },
  approveDoctor: async (profileId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.post<ApiResponse<null>>(`/admin/doctors/${profileId}/approve`, {})
    return response.data
  },
  rejectDoctor: async (profileId: string, rejectionReason: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.post<ApiResponse<null>>(`/admin/doctors/${profileId}/reject`, {
      rejection_reason: rejectionReason
    })
    return response.data
  },
}
