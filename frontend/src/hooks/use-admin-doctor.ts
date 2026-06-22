import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminDoctorService } from '@/services/admin-doctor.service'
import { AdminDoctorListResponse, DoctorVerificationResponse } from '@/types'

export function usePendingDoctors() {
  return useQuery<AdminDoctorListResponse[]>({
    queryKey: ['admin', 'doctors', 'pending'],
    queryFn: async () => {
      const response = await adminDoctorService.getPendingDoctors()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch pending applications')
    },
    staleTime: 15_000,
    refetchOnWindowFocus: true,
  })
}

export function useDoctorDetail(profileId: string | null) {
  return useQuery<DoctorVerificationResponse | null>({
    queryKey: ['admin', 'doctors', 'detail', profileId],
    queryFn: async () => {
      if (!profileId) return null
      const response = await adminDoctorService.getDoctorDetail(profileId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor detail')
    },
    enabled: !!profileId,
    staleTime: 30_000,
  })
}

export function useApproveDoctor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (profileId: string) => {
      const response = await adminDoctorService.approveDoctor(profileId)
      if (response.success) {
        return response
      }
      throw new Error(response.message || 'Failed to approve doctor')
    },
    onSuccess: (_, profileId) => {
      // Invalidate pending queue and dashboard cache
      queryClient.invalidateQueries({ queryKey: ['admin', 'doctors', 'pending'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'doctors', 'detail', profileId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'admin'] })
    },
  })
}

export function useRejectDoctor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ profileId, reason }: { profileId: string; reason: string }) => {
      const response = await adminDoctorService.rejectDoctor(profileId, reason)
      if (response.success) {
        return response
      }
      throw new Error(response.message || 'Failed to reject doctor')
    },
    onSuccess: (_, variables) => {
      // Invalidate pending queue and dashboard cache
      queryClient.invalidateQueries({ queryKey: ['admin', 'doctors', 'pending'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'doctors', 'detail', variables.profileId] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'admin'] })
    },
  })
}
