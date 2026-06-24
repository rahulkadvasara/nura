import apiClient from '@/lib/axios'
import { ApiResponse, User } from '@/types'

export const adminUserService = {
  listUsers: async (
    search?: string,
    role?: string,
    isActive?: boolean,
    limit?: number,
    skip?: number
  ): Promise<ApiResponse<User[]>> => {
    const params: any = {}
    if (search) params.search = search
    if (role) params.role = role
    if (isActive !== undefined) params.is_active = isActive
    if (limit !== undefined) params.limit = limit
    if (skip !== undefined) params.skip = skip

    const response = await apiClient.get<ApiResponse<{ users: User[] }>>('/admin/users', { params })
    return {
      success: response.data.success,
      message: response.data.message,
      data: response.data.data?.users || [],
      errors: response.data.errors
    }
  },

  getUserDetail: async (userId: string): Promise<ApiResponse<User>> => {
    const response = await apiClient.get<ApiResponse<User>>(`/admin/users/${userId}`)
    return response.data
  },

  activateUser: async (userId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.put<ApiResponse<null>>(`/admin/users/${userId}/activate`)
    return response.data
  },

  suspendUser: async (userId: string): Promise<ApiResponse<null>> => {
    const response = await apiClient.put<ApiResponse<null>>(`/admin/users/${userId}/suspend`)
    return response.data
  }
}
