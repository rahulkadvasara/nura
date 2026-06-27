import apiClient from '@/lib/axios'

export interface ReportResponse {
  id: string
  patient_id: string
  uploaded_by: string
  report_type: string
  file_url: string
  raw_text?: string
  normalized_text?: string
  risk_level: string
  processing_status: string
  ocr_status?: string
  ocr_method?: string
  ocr_average_confidence?: number
  ocr_duration_ms?: number
  ocr_completed_at?: string
  page_count?: number
  ocr_version?: string
  processing_errors?: string[]
  ocr_pages?: Record<string, any>[]
  created_at: string
  updated_at: string
}

export interface ReportProcessingStatus {
  report_id: string
  ocr_status: string
  processing_status: string
  ocr_method: string
  page_count: number
  ocr_average_confidence: number
  ocr_duration_ms: number
  processing_errors: string[]
}

export interface ReportOcrData {
  report_id: string
  raw_text: string
  normalized_text: string
  ocr_pages: Record<string, any>[]
  metadata: {
    ocr_method: string
    ocr_completed_at: string
    ocr_average_confidence: number
    page_count: number
    ocr_version: string
  }
}

export interface ReportTelemetryStats {
  uploaded_documents: number
  processed_pages: number
  ocr_latency_average_ms: number
  average_confidence: number
  failures: number
  retries: number
  extraction_methods: Record<string, number>
  average_processing_time_ms: number
}

export const reportService = {
  getReports: async (patientId?: string): Promise<ReportResponse[]> => {
    const params = patientId ? { patient_id: patientId } : {}
    const response = await apiClient.get<{ success: boolean; data: { reports: ReportResponse[] } }>('/reports', { params })
    return response.data.data.reports
  },

  uploadReport: async (patientId: string, reportType: string, file: File): Promise<ReportResponse> => {
    const formData = new FormData()
    formData.append('patient_id', patientId)
    formData.append('report_type', reportType)
    formData.append('file', file)

    const response = await apiClient.post<{ success: boolean; data: { report: ReportResponse } }>('/reports', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data.data.report
  },

  deleteReport: async (reportId: string): Promise<boolean> => {
    const response = await apiClient.delete<{ success: boolean }>((`/reports/${reportId}`))
    return response.data.success
  },

  processReport: async (reportId: string): Promise<boolean> => {
    const response = await apiClient.post<{ success: boolean }>((`/reports/${reportId}/process`))
    return response.data.success
  },

  getProcessingStatus: async (reportId: string): Promise<ReportProcessingStatus> => {
    const response = await apiClient.get<{ success: boolean; data: ReportProcessingStatus }>((`/reports/${reportId}/processing-status`))
    return response.data.data
  },

  getOcrResults: async (reportId: string): Promise<ReportOcrData> => {
    const response = await apiClient.get<{ success: boolean; data: ReportOcrData }>((`/reports/${reportId}/ocr`))
    return response.data.data
  },

  getProcessingTelemetry: async (): Promise<ReportTelemetryStats> => {
    const response = await apiClient.get<{ success: boolean; data: ReportTelemetryStats }>('/reports/telemetry/statistics')
    return response.data.data
  },
}
