import apiClient from '@/lib/axios'
import {
  ApiResponse,
  PlatformHealthResponse,
  SystemInfoResponse,
  BackgroundJobResponse,
  MaintenanceActionResponse,
} from '@/types'

export const systemMonitorService = {
  getSystemHealth: async (): Promise<ApiResponse<PlatformHealthResponse>> => {
    const response = await apiClient.get<ApiResponse<PlatformHealthResponse>>('/admin/system/health')
    return response.data
  },

  getSystemInfo: async (): Promise<ApiResponse<SystemInfoResponse>> => {
    const response = await apiClient.get<ApiResponse<SystemInfoResponse>>('/admin/system/info')
    return response.data
  },

  getBackgroundJobs: async (): Promise<ApiResponse<BackgroundJobResponse>> => {
    const response = await apiClient.get<ApiResponse<BackgroundJobResponse>>('/admin/system/jobs')
    return response.data
  },

  runMaintenanceAction: async (
    actionType: 'clear-sessions' | 'clear-otps' | 'archive-notifications' | 'archive-audit-logs',
    params?: { retention_days?: number }
  ): Promise<ApiResponse<MaintenanceActionResponse>> => {
    const response = await apiClient.post<ApiResponse<MaintenanceActionResponse>>(
      `/admin/system/maintenance/${actionType}`,
      null,
      { params }
    )
    return response.data
  },
}
