import apiClient from '@/lib/axios'
import { ApiResponse, PatientDashboardData } from '@/types'

export const dashboardService = {
  getPatientDashboard: async (): Promise<ApiResponse<PatientDashboardData>> => {
    const response = await apiClient.get<ApiResponse<PatientDashboardData>>('/dashboard/patient')
    return response.data
  },
}
