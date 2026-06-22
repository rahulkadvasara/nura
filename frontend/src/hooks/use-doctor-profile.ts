import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorProfileService, DoctorProfileManagementUpdateRequest, DoctorProfileManagementResponseData } from '@/services/doctor-profile.service'

export function useDoctorProfile() {
  return useQuery<DoctorProfileManagementResponseData>({
    queryKey: ['doctor', 'profile'],
    queryFn: async () => {
      const response = await doctorProfileService.getDoctorProfile()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor profile')
    },
    staleTime: 30_000,
  })
}

export function useUpdateDoctorProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (profile: DoctorProfileManagementUpdateRequest) => {
      const response = await doctorProfileService.updateDoctorProfile(profile)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to update doctor profile')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'profile'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard', 'doctor'] })
    },
  })
}
