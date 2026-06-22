import { useQuery } from '@tanstack/react-query'
import {
  doctorDiscoveryService,
  DoctorDiscoveryResponseData,
  DoctorsListResponse,
  DoctorAvailabilityListResponse,
} from '@/services/doctor-discovery.service'

export function useDoctors(filters?: {
  search?: string
  specialization?: string
  min_experience?: number
}) {
  return useQuery<DoctorsListResponse>({
    queryKey: ['doctors', 'list', filters],
    queryFn: async () => {
      const response = await doctorDiscoveryService.getDoctors(filters)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctors')
    },
    staleTime: 60_000, // Cache for 1 minute
  })
}

export function useDoctorDetails(doctorId: string) {
  return useQuery<DoctorDiscoveryResponseData>({
    queryKey: ['doctors', 'details', doctorId],
    queryFn: async () => {
      const response = await doctorDiscoveryService.getDoctorDetails(doctorId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor details')
    },
    enabled: !!doctorId,
    staleTime: 60_000,
  })
}

export function useDoctorAvailability(doctorId: string) {
  return useQuery<DoctorAvailabilityListResponse>({
    queryKey: ['doctors', 'availability', doctorId],
    queryFn: async () => {
      const response = await doctorDiscoveryService.getDoctorAvailability(doctorId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch doctor availability')
    },
    enabled: !!doctorId,
    staleTime: 30_000, // Refresh slots slightly faster
  })
}
