import { useQuery, useMutation } from '@tanstack/react-query'
import { 
  aiService, 
  AIHealthResponse, 
  AITestResponse, 
  EmbeddingHealthResponse, 
  EmbeddingTestResponse,
  VectorCollectionInfo,
  VectorHealthResponse,
  VectorTestResponse
} from '@/services/ai.service'

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

/**
 * Custom hook to monitor backend embedding status periodically.
 */
export function useEmbeddingHealth() {
  return useQuery<EmbeddingHealthResponse, Error>({
    queryKey: ['admin', 'ai', 'embeddings', 'health'],
    queryFn: async () => {
      return await aiService.getEmbeddingHealth()
    },
    refetchInterval: 30000, // Refresh status check every 30 seconds
  })
}

/**
 * Custom hook to trigger text vectorization tests against the embedding console.
 */
export function useEmbeddingTest() {
  return useMutation<EmbeddingTestResponse, Error, string>({
    mutationFn: async (text: string) => {
      return await aiService.testEmbeddingPlayground(text)
    }
  })
}

/**
 * Custom hook to monitor backend vector health and collection statistics periodically.
 */
export function useVectorHealth() {
  return useQuery<VectorHealthResponse, Error>({
    queryKey: ['admin', 'ai', 'vector', 'health'],
    queryFn: async () => {
      return await aiService.getVectorHealth()
    },
    refetchInterval: 30000, // Refresh status check every 30 seconds
  })
}

/**
 * Custom hook to fetch all vector database collections setup.
 */
export function useVectorCollections() {
  return useQuery<VectorCollectionInfo[], Error>({
    queryKey: ['admin', 'ai', 'vector', 'collections'],
    queryFn: async () => {
      return await aiService.getVectorCollections()
    }
  })
}

/**
 * Custom hook to execute roundtrip verification test of the vector pipeline.
 */
export function useVectorTest() {
  return useMutation<VectorTestResponse, Error, { collection: string; text: string }>({
    mutationFn: async ({ collection, text }) => {
      return await aiService.testVectorSearch(collection, text)
    }
  })
}
