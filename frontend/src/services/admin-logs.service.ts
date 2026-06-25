import apiClient from '@/lib/axios'
import { ApiResponse, AuditLog, AgentLog } from '@/types'

export interface LogsListResponse<T> {
  logs: T[]
  total: number
  limit: number
  skip: number
}

export const adminLogsService = {
  getAuditLogs: async (params?: {
    limit?: number
    skip?: number
    search?: string
    user_id?: string
    role?: string
    action?: string
    resource_type?: string
    start_date?: string
    end_date?: string
  }): Promise<ApiResponse<LogsListResponse<AuditLog>>> => {
    const response = await apiClient.get<ApiResponse<LogsListResponse<AuditLog>>>('/admin/logs/audit', { params })
    return response.data
  },

  getAuditLogDetail: async (id: string): Promise<ApiResponse<AuditLog>> => {
    const response = await apiClient.get<ApiResponse<AuditLog>>(`/admin/logs/audit/${id}`)
    return response.data
  },

  getAgentLogs: async (params?: {
    limit?: number
    skip?: number
    agent?: string
    status?: string
    session?: string
    start_date?: string
    end_date?: string
  }): Promise<ApiResponse<LogsListResponse<AgentLog>>> => {
    const queryParams = {
      limit: params?.limit,
      skip: params?.skip,
      agent: params?.agent,
      status_filter: params?.status,
      session: params?.session,
      start_date: params?.start_date,
      end_date: params?.end_date,
    }
    const response = await apiClient.get<ApiResponse<LogsListResponse<AgentLog>>>('/admin/logs/agents', { params: queryParams })
    return response.data
  },

  getAgentLogDetail: async (id: string): Promise<ApiResponse<AgentLog>> => {
    const response = await apiClient.get<ApiResponse<AgentLog>>(`/admin/logs/agents/${id}`)
    return response.data
  },

  getAuthLogs: async (params?: {
    limit?: number
    skip?: number
    search?: string
    start_date?: string
    end_date?: string
  }): Promise<ApiResponse<LogsListResponse<AuditLog>>> => {
    const response = await apiClient.get<ApiResponse<LogsListResponse<AuditLog>>>('/admin/logs/authentication', { params })
    return response.data
  },
}
