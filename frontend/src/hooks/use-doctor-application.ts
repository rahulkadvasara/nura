import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorApplicationService } from '@/services/doctor-application.service'
import { DoctorApplicationRequest, DoctorApplicationUpdateRequest, DoctorApplicationData } from '@/types'

export function useDoctorApplication() {
  return useQuery<DoctorApplicationData | null>({
    queryKey: ['doctor-application'],
    queryFn: async () => {
      try {
        const response = await doctorApplicationService.getDoctorApplication()
        if (response.success && response.data) {
          return response.data
        }
        return null
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null
        }
        throw new Error(error.response?.data?.message || error.message || 'Failed to load doctor application status')
      }
    },
    retry: false, // If it returns 404, we don't need to retry
    staleTime: 30_000,
    refetchOnWindowFocus: true,
  })
}

export function useApplyAsDoctor() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: DoctorApplicationRequest) => {
      const response = await doctorApplicationService.applyAsDoctor(data)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to submit doctor application')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-application'] })
    },
  })
}

export function useUpdateDoctorApplication() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: DoctorApplicationUpdateRequest) => {
      const response = await doctorApplicationService.updateDoctorApplication(data)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to update doctor application')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor-application'] })
    },
  })
}
