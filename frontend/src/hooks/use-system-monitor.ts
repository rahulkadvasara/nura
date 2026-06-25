import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { systemMonitorService } from '@/services/system-monitor.service'
import {
  PlatformHealthResponse,
  SystemInfoResponse,
  BackgroundJobResponse,
  MaintenanceActionResponse,
} from '@/types'

export function useSystemHealth() {
  return useQuery<PlatformHealthResponse>({
    queryKey: ['admin', 'system', 'health'],
    queryFn: async () => {
      const response = await systemMonitorService.getSystemHealth()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch system health status')
    },
    refetchInterval: 15000, // Poll health status every 15 seconds
  })
}

export function useSystemInfo() {
  return useQuery<SystemInfoResponse>({
    queryKey: ['admin', 'system', 'info'],
    queryFn: async () => {
      const response = await systemMonitorService.getSystemInfo()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch system info')
    },
    staleTime: Infinity, // System info configuration environment remains static
  })
}

export function useBackgroundJobs() {
  return useQuery<BackgroundJobResponse>({
    queryKey: ['admin', 'system', 'jobs'],
    queryFn: async () => {
      const response = await systemMonitorService.getBackgroundJobs()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch background jobs status')
    },
    refetchInterval: 15000, // Poll background job statistics every 15 seconds
  })
}

export function useMaintenanceAction() {
  const queryClient = useQueryClient()
  return useMutation<
    MaintenanceActionResponse,
    Error,
    {
      actionType: 'clear-sessions' | 'clear-otps' | 'archive-notifications' | 'archive-audit-logs'
      retentionDays?: number
    }
  >({
    mutationFn: async ({ actionType, retentionDays }) => {
      const response = await systemMonitorService.runMaintenanceAction(actionType, { retention_days: retentionDays })
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to execute maintenance action')
    },
    onSuccess: () => {
      // Invalidate system health and background task queries to refresh active counts
      queryClient.invalidateQueries({ queryKey: ['admin', 'system'] })
    },
  })
}
