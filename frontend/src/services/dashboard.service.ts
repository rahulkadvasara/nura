import apiClient from '@/lib/axios'
import { ApiResponse, PatientDashboardData, DoctorDashboardData } from '@/types'

export const dashboardService = {
  getPatientDashboard: async (): Promise<ApiResponse<PatientDashboardData>> => {
    const response = await apiClient.get<ApiResponse<PatientDashboardData>>('/dashboard/patient')
    return response.data
  },
  getDoctorDashboard: async (): Promise<ApiResponse<DoctorDashboardData>> => {
    const response = await apiClient.get<ApiResponse<DoctorDashboardData>>('/dashboard/doctor')
    return response.data
  },
}

