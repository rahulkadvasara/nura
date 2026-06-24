import apiClient from '@/lib/axios'
import {
  ApiResponse,
  User,
  AdminCreateRequest,
  AdminCreateResponse,
  AdminDetailResponse,
  AdminSession,
} from '@/types'

export const adminManagementService = {
  listAdmins: async (): Promise<ApiResponse<User[]>> => {
    const response = await apiClient.get<ApiResponse<{ admins: User[] }>>('/admin/admins')
    return {
      success: response.data.success,
      message: response.data.message,
      data: response.data.data?.admins || [],
      errors: response.data.errors,
    }
  },

  getAdminDetail: async (adminId: string): Promise<ApiResponse<AdminDetailResponse>> => {
    const response = await apiClient.get<ApiResponse<AdminDetailResponse>>(`/admin/admins/${adminId}`)
    return response.data
  },

  createAdmin: async (data: AdminCreateRequest): Promise<ApiResponse<AdminCreateResponse>> => {
    const response = await apiClient.post<ApiResponse<AdminCreateResponse>>('/admin/admins', data)
    return response.data
  },

  enableAdmin: async (adminId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.put<ApiResponse<null>>(`/admin/admins/${adminId}/enable`)
    return response.data
  },

  disableAdmin: async (adminId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.put<ApiResponse<null>>(`/admin/admins/${adminId}/disable`)
    return response.data
  },

  listSessions: async (): Promise<ApiResponse<AdminSession[]>> => {
    const response = await apiClient.get<ApiResponse<{ sessions: AdminSession[] }>>('/admin/security/sessions')
    return {
      success: response.data.success,
      message: response.data.message,
      data: response.data.data?.sessions || [],
      errors: response.data.errors,
    }
  },

  revokeSession: async (sessionId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.post<ApiResponse<null>>(`/admin/security/sessions/${sessionId}/revoke`)
    return response.data
  },
}

