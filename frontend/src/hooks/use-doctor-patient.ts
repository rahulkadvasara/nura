import { useQuery } from '@tanstack/react-query'
import { doctorPatientService } from '@/services/doctor-patient.service'
import { DoctorPatientListResponse, DoctorPatientDetail } from '@/types'

export function useDoctorPatients(params: {
  search?: string
  sort_by?: string
  limit?: number
  skip?: number
}) {
  return useQuery<DoctorPatientListResponse>({
    queryKey: ['doctor', 'patients', params],
    queryFn: async () => {
      const response = await doctorPatientService.getPatients(params)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch patients list')
    },
    placeholderData: (previousData) => previousData,
  })
}

export function useDoctorPatient(patientId: string) {
  return useQuery<DoctorPatientDetail>({
    queryKey: ['doctor', 'patient', patientId],
    queryFn: async () => {
      const response = await doctorPatientService.getPatientDetail(patientId)
      if (response.success && response.data) {
        return response.data
      }
      throw new Error(response.message || 'Failed to fetch patient details')
    },
    enabled: !!patientId,
  })
}
