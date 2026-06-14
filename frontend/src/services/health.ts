import { apiClient } from '@/lib/axios'

export interface HealthResponse {
  status: string
  app: string
  environment: string
  mongodb: string
  qdrant: string
}

export const healthService = {
  checkHealth: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/health')
    return response.data
  }
}