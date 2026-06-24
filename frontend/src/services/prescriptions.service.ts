import apiClient from '@/lib/axios'
import {
  ApiResponse,
  Prescription,
  PrescriptionCreateRequest,
  PrescriptionUpdateRequest,
  PatientConsultationItem,
  PatientPrescription,
} from '@/types'

export const prescriptionsService = {
  createPrescription: async (
    consultationId: string,
    payload: PrescriptionCreateRequest
  ): Promise<ApiResponse<Prescription>> => {
    const response = await apiClient.post<ApiResponse<Prescription>>(
      `/doctor/consultations/${consultationId}/prescription`,
      payload
    )
    return response.data
  },

  updatePrescription: async (
    prescriptionId: string,
    payload: PrescriptionUpdateRequest
  ): Promise<ApiResponse<Prescription>> => {
    const response = await apiClient.put<ApiResponse<Prescription>>(
      `/doctor/prescriptions/${prescriptionId}`,
      payload
    )
    return response.data
  },

  getDoctorPrescriptions: async (): Promise<ApiResponse<{ prescriptions: Prescription[] }>> => {
    const response = await apiClient.get<ApiResponse<{ prescriptions: Prescription[] }>>(
      '/doctor/prescriptions'
    )
    return response.data
  },

  getDoctorPrescriptionDetails: async (prescriptionId: string): Promise<ApiResponse<Prescription>> => {
    const response = await apiClient.get<ApiResponse<Prescription>>(
      `/doctor/prescriptions/${prescriptionId}`
    )
    return response.data
  },

  getPatientConsultations: async (): Promise<ApiResponse<{ consultations: PatientConsultationItem[] }>> => {
    const response = await apiClient.get<ApiResponse<{ consultations: PatientConsultationItem[] }>>(
      '/patient/consultations'
    )
    return response.data
  },

  getPatientConsultationDetails: async (consultationId: string): Promise<ApiResponse<PatientConsultationItem>> => {
    const response = await apiClient.get<ApiResponse<PatientConsultationItem>>(
      `/patient/consultations/${consultationId}`
    )
    return response.data
  },

  getPatientPrescriptions: async (): Promise<ApiResponse<{ prescriptions: PatientPrescription[] }>> => {
    const response = await apiClient.get<ApiResponse<{ prescriptions: PatientPrescription[] }>>(
      '/patient/prescriptions'
    )
    return response.data
  },

  getPatientPrescriptionDetails: async (prescriptionId: string): Promise<ApiResponse<PatientPrescription>> => {
    const response = await apiClient.get<ApiResponse<PatientPrescription>>(
      `/patient/prescriptions/${prescriptionId}`
    )
    return response.data
  },
}
