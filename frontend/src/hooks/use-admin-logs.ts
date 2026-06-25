import { useQuery } from '@tanstack/react-query'
import { adminLogsService, LogsListResponse } from '@/services/admin-logs.service'
import { AuditLog, AgentLog } from '@/types'

export function useAuditLogs(params?: {
  limit?: number
  skip?: number
  search?: string
  user_id?: string
  role?: string
  action?: string
  resource_type?: string
  start_date?: string
  end_date?: string
}) {
  return useQuery<LogsListResponse<AuditLog>>({
    queryKey: ['admin', 'logs', 'audit', params],
    queryFn: async () => {
      const response = await adminLogsService.getAuditLogs(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch audit logs')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useAuditLog(id: string) {
  return useQuery<AuditLog>({
    queryKey: ['admin', 'logs', 'audit', id],
    queryFn: async () => {
      const response = await adminLogsService.getAuditLogDetail(id)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch audit log detail')
    },
    enabled: !!id,
  })
}

export function useAgentLogs(params?: {
  limit?: number
  skip?: number
  agent?: string
  status?: string
  session?: string
  start_date?: string
  end_date?: string
}) {
  return useQuery<LogsListResponse<AgentLog>>({
    queryKey: ['admin', 'logs', 'agents', params],
    queryFn: async () => {
      const response = await adminLogsService.getAgentLogs(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch agent logs')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useAgentLog(id: string) {
  return useQuery<AgentLog>({
    queryKey: ['admin', 'logs', 'agents', id],
    queryFn: async () => {
      const response = await adminLogsService.getAgentLogDetail(id)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch agent log detail')
    },
    enabled: !!id,
  })
}

export function useAuthenticationLogs(params?: {
  limit?: number
  skip?: number
  search?: string
  start_date?: string
  end_date?: string
}) {
  return useQuery<LogsListResponse<AuditLog>>({
    queryKey: ['admin', 'logs', 'authentication', params],
    queryFn: async () => {
      const response = await adminLogsService.getAuthLogs(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch authentication logs')
    },
    placeholderData: (previousData) => previousData,
  })
}
