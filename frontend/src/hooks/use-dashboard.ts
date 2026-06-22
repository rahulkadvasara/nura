import { useQuery } from '@tanstack/react-query'
import { dashboardService } from '@/services/dashboard.service'
import { PatientDashboardData, DoctorDashboardData } from '@/types'

export function usePatientDashboard() {
  return useQuery<PatientDashboardData>({
    queryKey: ['dashboard', 'patient'],
    queryFn: async () => {
      const response = await dashboardService.getPatientDashboard()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to load dashboard')
    },
    staleTime: 30_000, // 30 seconds
    refetchOnWindowFocus: true,
  })
}

export function useDoctorDashboard() {
  return useQuery<DoctorDashboardData>({
    queryKey: ['dashboard', 'doctor'],
    queryFn: async () => {
      const response = await dashboardService.getDoctorDashboard()
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to load dashboard')
    },
    staleTime: 30_000, // 30 seconds
    refetchOnWindowFocus: true,
  })
}

