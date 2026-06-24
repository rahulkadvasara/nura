import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { prescriptionsService } from '@/services/prescriptions.service'
import { PrescriptionCreateRequest, PrescriptionUpdateRequest } from '@/types'

export function useCreatePrescription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ consultationId, payload }: { consultationId: string; payload: PrescriptionCreateRequest }) => {
      const response = await prescriptionsService.createPrescription(consultationId, payload)
      if (response.success && response.data) return response.data
      throw new Error(response.message || 'Failed to create prescription')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions'] })
      queryClient.invalidateQueries({ queryKey: ['consultations'] })
      queryClient.invalidateQueries({ queryKey: ['doctor', 'dashboard'] })
    },
  })
}

export function useUpdatePrescription() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ prescriptionId, payload }: { prescriptionId: string; payload: PrescriptionUpdateRequest }) => {
      const response = await prescriptionsService.updatePrescription(prescriptionId, payload)
      if (response.success && response.data) return response.data
      throw new Error(response.message || 'Failed to update prescription')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prescriptions'] })
      queryClient.invalidateQueries({ queryKey: ['consultations'] })
    },
  })
}

export function useDoctorPrescriptions() {
  return useQuery({
    queryKey: ['prescriptions', 'doctor'],
    queryFn: async () => {
      const response = await prescriptionsService.getDoctorPrescriptions()
      if (response.success && response.data) return response.data.prescriptions
      throw new Error(response.message || 'Failed to fetch prescriptions')
    },
  })
}

export function useDoctorPrescriptionDetails(prescriptionId: string) {
  return useQuery({
    queryKey: ['prescription', 'doctor', prescriptionId],
    queryFn: async () => {
      const response = await prescriptionsService.getDoctorPrescriptionDetails(prescriptionId)
      if (response.success && response.data) return response.data
      throw new Error(response.message || 'Failed to fetch prescription details')
    },
    enabled: !!prescriptionId,
  })
}

export function usePatientConsultations() {
  return useQuery({
    queryKey: ['consultations', 'patient'],
    queryFn: async () => {
      const response = await prescriptionsService.getPatientConsultations()
      if (response.success && response.data) return response.data.consultations
      throw new Error(response.message || 'Failed to fetch consultation history')
    },
  })
}

export function usePatientConsultationDetails(consultationId: string) {
  return useQuery({
    queryKey: ['consultation', 'patient', consultationId],
    queryFn: async () => {
      const response = await prescriptionsService.getPatientConsultationDetails(consultationId)
      if (response.success && response.data) return response.data
      throw new Error(response.message || 'Failed to fetch consultation details')
    },
    enabled: !!consultationId,
  })
}

export function usePatientPrescriptions() {
  return useQuery({
    queryKey: ['prescriptions', 'patient'],
    queryFn: async () => {
      const response = await prescriptionsService.getPatientPrescriptions()
      if (response.success && response.data) return response.data.prescriptions
      throw new Error(response.message || 'Failed to fetch prescriptions')
    },
  })
}

export function usePatientPrescriptionDetails(prescriptionId: string) {
  return useQuery({
    queryKey: ['prescription', 'patient', prescriptionId],
    queryFn: async () => {
      const response = await prescriptionsService.getPatientPrescriptionDetails(prescriptionId)
      if (response.success && response.data) return response.data
      throw new Error(response.message || 'Failed to fetch prescription details')
    },
    enabled: !!prescriptionId,
  })
}
