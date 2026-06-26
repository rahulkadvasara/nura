import { useQuery, useMutation } from '@tanstack/react-query'
import { aiService, AIHealthResponse, AITestResponse } from '@/services/ai.service'

/**
 * Custom hook to monitor backend AI status periodically.
 */
export function useAIHealth() {
  return useQuery<AIHealthResponse, Error>({
    queryKey: ['admin', 'ai', 'health'],
    queryFn: async () => {
      return await aiService.getAIHealth()
    },
    refetchInterval: 30000, // Refresh status check every 30 seconds
  })
}

/**
 * Custom hook to trigger prompt execution against the AI playground.
 */
export function useAIPlaygroundTest() {
  return useMutation<AITestResponse, Error, string>({
    mutationFn: async (prompt: string) => {
      return await aiService.testAIPlayground(prompt)
    }
  })
}
