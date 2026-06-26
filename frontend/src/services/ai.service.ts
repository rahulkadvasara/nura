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
  }
}
