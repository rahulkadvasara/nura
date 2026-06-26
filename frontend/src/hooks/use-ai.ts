import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  aiService, 
  AIHealthResponse, 
  AITestResponse, 
  EmbeddingHealthResponse, 
  EmbeddingTestResponse,
  VectorCollectionInfo,
  VectorHealthResponse,
  VectorTestResponse,
  PatientContextResponse,
  AIPlaygroundHealthResponse,
  AIPlaygroundChatResponse,
  AIPlaygroundChatRequest,
  DocumentIndexRequest,
  DocumentIndexResponse,
  BatchDocumentIndexRequest,
  BatchDocumentIndexResponse,
  IndexingStatisticsResponse,
  IndexDeletionResponse,
  RetrievalRequest,
  RetrievalResponse,
  RetrievalStatisticsResponse
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

/**
 * Custom hook to trigger patient context assembly.
 */
export function usePatientContext() {
  return useMutation<PatientContextResponse, Error, string | undefined>({
    mutationFn: async (patientId?: string) => {
      return await aiService.getPatientContext(patientId)
    }
  })
}

/**
 * Custom hook to monitor backend integrated AI playground health periodically.
 */
export function useAIPlaygroundHealth() {
  return useQuery<AIPlaygroundHealthResponse, Error>({
    queryKey: ['admin', 'ai', 'playground', 'health'],
    queryFn: async () => {
      return await aiService.getAIPlaygroundHealth()
    },
    refetchInterval: 30000, // Refresh status check every 30 seconds
  })
}

/**
 * Custom hook to trigger a playground chat session execution.
 */
export function useAIPlaygroundChat() {
  return useMutation<AIPlaygroundChatResponse, Error, AIPlaygroundChatRequest>({
    mutationFn: async (request: AIPlaygroundChatRequest) => {
      return await aiService.testAIPlaygroundChat(request)
    }
  })
}

/**
 * Custom hook to fetch document indexing pipeline statistics.
 */
export function useIndexStatistics() {
  return useQuery<IndexingStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'indexing', 'statistics'],
    queryFn: async () => {
      return await aiService.getIndexStatistics()
    },
    refetchInterval: 15000, // Refresh metrics every 15 seconds
  })
}

/**
 * Custom hook to trigger single document indexing.
 */
export function useIndexDocument() {
  const queryClient = useQueryClient()
  return useMutation<DocumentIndexResponse, Error, DocumentIndexRequest>({
    mutationFn: async (request: DocumentIndexRequest) => {
      return await aiService.indexDocument(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'indexing', 'statistics'] })
    }
  })
}

/**
 * Custom hook to trigger batch document indexing.
 */
export function useBatchIndexDocuments() {
  const queryClient = useQueryClient()
  return useMutation<BatchDocumentIndexResponse, Error, BatchDocumentIndexRequest>({
    mutationFn: async (request: BatchDocumentIndexRequest) => {
      return await aiService.batchIndexDocuments(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'indexing', 'statistics'] })
    }
  })
}

/**
 * Custom hook to trigger document reindexing.
 */
export function useReindexDocument() {
  const queryClient = useQueryClient()
  return useMutation<DocumentIndexResponse, Error, DocumentIndexRequest>({
    mutationFn: async (request: DocumentIndexRequest) => {
      return await aiService.reindexDocument(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'indexing', 'statistics'] })
    }
  })
}

/**
 * Custom hook to delete a specific document vector.
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation<IndexDeletionResponse, Error, { documentId: string; documentType: string }>({
    mutationFn: async ({ documentId, documentType }) => {
      return await aiService.deleteDocument(documentId, documentType)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'indexing', 'statistics'] })
    }
  })
}

/**
 * Custom hook to delete all patient reports vectors.
 */
export function useDeletePatientDocuments() {
  const queryClient = useQueryClient()
  return useMutation<IndexDeletionResponse, Error, string>({
    mutationFn: async (patientId: string) => {
      return await aiService.deletePatientDocuments(patientId)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'indexing', 'statistics'] })
    }
  })
}

/**
 * Custom hook to execute single-collection semantic retrieval.
 */
export function useRetrieval() {
  const queryClient = useQueryClient()
  return useMutation<RetrievalResponse, Error, RetrievalRequest>({
    mutationFn: async (request: RetrievalRequest) => {
      return await aiService.retrieve(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'retrieval', 'statistics'] })
    }
  })
}

/**
 * Custom hook to execute multi-collection semantic retrieval.
 */
export function useRetrievalMulti() {
  const queryClient = useQueryClient()
  return useMutation<RetrievalResponse, Error, RetrievalRequest>({
    mutationFn: async (request: RetrievalRequest) => {
      return await aiService.retrieveMulti(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'retrieval', 'statistics'] })
    }
  })
}

/**
 * Custom hook to monitor retrieval metrics statistics periodically.
 */
export function useRetrievalStatistics() {
  return useQuery<RetrievalStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'retrieval', 'statistics'],
    queryFn: async () => {
      return await aiService.getRetrievalStatistics()
    },
    refetchInterval: 15000 // Refresh retrieval stats every 15 seconds
  })
}

