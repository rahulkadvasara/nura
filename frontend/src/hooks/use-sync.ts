import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  aiService,
  SyncStatusResponse,
  SyncPatientResponse,
  SyncRebuildResponse,
  SyncStatisticsResponse,
} from '@/services/ai.service'

/**
 * Custom hook to monitor patient memory sync queue and DLQ status.
 */
export function useSyncStatus() {
  return useQuery<SyncStatusResponse, Error>({
    queryKey: ['admin', 'ai', 'sync', 'status'],
    queryFn: async () => {
      return await aiService.getSyncStatus()
    },
    refetchInterval: 10000, // Refresh status check every 10 seconds
  })
}

/**
 * Custom hook to trigger synchronization for a specific patient.
 */
export function useSyncPatient() {
  const queryClient = useQueryClient()
  return useMutation<SyncPatientResponse, Error, string>({
    mutationFn: async (patientId: string) => {
      return await aiService.syncPatient(patientId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'sync', 'status'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'sync', 'statistics'] })
    }
  })
}

/**
 * Custom hook to trigger full platform background sync rebuild for all patients.
 */
export function useRebuildSync() {
  const queryClient = useQueryClient()
  return useMutation<SyncRebuildResponse, Error, void>({
    mutationFn: async () => {
      return await aiService.rebuildSync()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'sync', 'status'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'sync', 'statistics'] })
    }
  })
}

/**
 * Custom hook to monitor patient memory sync pipeline telemetry statistics.
 */
export function useSyncStatistics() {
  return useQuery<SyncStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'sync', 'statistics'],
    queryFn: async () => {
      return await aiService.getSyncStatistics()
    },
    refetchInterval: 10000, // Refresh stats every 10 seconds
  })
}
