import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { doctorAvailabilityService } from '@/services/doctor-availability.service'
import { DoctorAvailability, DoctorAvailabilityCreateRequest, DoctorAvailabilityUpdateRequest } from '@/types'

export function useDoctorAvailability() {
  return useQuery<DoctorAvailability[]>({
    queryKey: ['doctor', 'availability'],
    queryFn: async () => {
      const response = await doctorAvailabilityService.getAvailability()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor availability')
    },
    staleTime: 10_000,
  })
}

export function useCreateAvailabilitySlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (slot: DoctorAvailabilityCreateRequest) => {
      const response = await doctorAvailabilityService.createAvailabilitySlot(slot)
      if (response.success) {
        return response
      }
      throw new Error(response.message || 'Failed to create availability slot')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'availability'] })
    },
  })
}

export function useUpdateAvailabilitySlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, slot }: { id: string; slot: DoctorAvailabilityUpdateRequest }) => {
      const response = await doctorAvailabilityService.updateAvailabilitySlot(id, slot)
      if (response.success) {
        return response
      }
      throw new Error(response.message || 'Failed to update availability slot')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'availability'] })
    },
  })
}

export function useDeleteAvailabilitySlot() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: string) => {
      const response = await doctorAvailabilityService.deleteAvailabilitySlot(id)
      if (response.success) {
        return response
      }
      throw new Error(response.message || 'Failed to delete availability slot')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['doctor', 'availability'] })
    },
  })
}
