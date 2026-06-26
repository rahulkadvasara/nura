import { apiClient } from '@/lib/axios'

export interface AIHealthResponse {
  reachable: boolean
  model: string
  latency_ms: number
  status: string
  timestamp: string
}

export interface AITestResponse {
  response: string
  model: string
  token_usage: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  latency: number
  finish_reason: string
}

export interface EmbeddingHealthResponse {
  provider: string
  model: string
  dimensions: number
  latency: number
  status: string
}

export interface EmbeddingTestResponse {
  dimensions: number
  vector_preview: number[]
  latency: number
  metadata: Record<string, any>
}

export interface VectorCollectionInfo {
  name: string
  status: string
  vector_count: number
  dimensions: number
  distance: string
  storage_bytes?: number
  last_update_time?: string
}

export interface VectorHealthResponse {
  connected: boolean
  latency: number
  collections: VectorCollectionInfo[]
}

export interface VectorTestResultItem {
  id: string
  score: number
  payload: Record<string, any>
}

export interface VectorTestResponse {
  latency: number
  search_results: VectorTestResultItem[]
  similarity_scores: number[]
}

export interface PatientContextMetadata {
  patient_id: string
  generated_at: string
  sources_used: string[]
  sections_returned: string[]
  estimated_tokens: number
  context_version: string
}

export interface PatientContextResponse {
  patient_profile?: Record<string, any>
  medical_summary?: string
  current_conditions: string[]
  past_medical_history: string[]
  current_medications: string[]
  medication_allergies: string[]
  drug_allergies: string[]
  lab_reports_summary: Record<string, any>[]
  appointments_summary: Record<string, any>[]
  consultations_summary: Record<string, any>[]
  prescriptions_summary: Record<string, any>[]
  reminder_summary: Record<string, any>[]
  recent_health_insights: Record<string, any>[]
  lifestyle_notes?: string
  emergency_information?: string
  risk_factors: string[]
  metadata: PatientContextMetadata
}

export const aiService = {
  /**
   * Retrieves connectivity and latency details from the AI backend health check.
   */
  getAIHealth: async (): Promise<AIHealthResponse> => {
    const response = await apiClient.get<AIHealthResponse>('/ai/health')
    return response.data
  },

  /**
   * Executes a direct prompt completion verification test. Admin accounts only.
   */
  testAIPlayground: async (prompt: string): Promise<AITestResponse> => {
    const response = await apiClient.post<AITestResponse>('/ai/test', { prompt })
    return response.data
  },

  /**
   * Retrieves connectivity details from the AI embedding health check.
   */
  getEmbeddingHealth: async (): Promise<EmbeddingHealthResponse> => {
    const response = await apiClient.get<EmbeddingHealthResponse>('/ai/embeddings/health')
    return response.data
  },

  /**
   * Generates a preview embedding and metadata. Admin accounts only.
   */
  testEmbeddingPlayground: async (text: string): Promise<EmbeddingTestResponse> => {
    const response = await apiClient.post<EmbeddingTestResponse>('/ai/embeddings/test', { text })
    return response.data
  },

  /**
   * Retrieves overall vector health status and collection stats. Admin accounts only.
   */
  getVectorHealth: async (): Promise<VectorHealthResponse> => {
    const response = await apiClient.get<VectorHealthResponse>('/ai/vector/health')
    return response.data
  },

  /**
   * Retrieves list of Qdrant collection specifications. Admin accounts only.
   */
  getVectorCollections: async (): Promise<VectorCollectionInfo[]> => {
    const response = await apiClient.get<VectorCollectionInfo[]>('/ai/vector/collections')
    return response.data
  },

  /**
   * Executes a roundtrip semantic query verification test. Admin accounts only.
   */
  testVectorSearch: async (collection: string, text: string): Promise<VectorTestResponse> => {
    const response = await apiClient.post<VectorTestResponse>('/ai/vector/test', { collection, text })
    return response.data
  },

  /**
   * Assembles a patient's complete structured AI context. Admin/Doctor accounts only (or Patient /context/me).
   */
  getPatientContext: async (patientId?: string): Promise<PatientContextResponse> => {
    const url = patientId ? `/ai/context/${patientId}` : '/ai/context/me'
    const response = await apiClient.get<PatientContextResponse>(url)
    return response.data
  }
}
