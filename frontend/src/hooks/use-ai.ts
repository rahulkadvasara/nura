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
  RetrievalStatisticsResponse,
  RetrievalPackage,
  RetrievalAgentStatisticsResponse,
  ContextAssemblyRequest,
  ContextAssemblyResponse,
  ContextAssemblyStatisticsResponse,
  GraphHealthResponse,
  GraphNodesResponse,
  GraphTestRunRequest,
  GraphTestRunResponse,
  GraphStatisticsResponse,
  RouterIntentsResponse,
  RouterClassifyRequest,
  RouterClassifyResponse,
  RouterTestRequest,
  RouterTestResponse,
  RouterStatisticsResponse,
  MedicalKnowledgeAgentResponse,
  SymptomAgentResponse,
  MemoryAgentResponse,
  ReportAnalysisAgentResponse,
  DrugInteractionAgentResponse,
  DoctorRecommendationAgentResponse
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
export function useRetrievalSingle() {
  const queryClient = useQueryClient()
  return useMutation<RetrievalResponse, Error, RetrievalRequest>({
    mutationFn: async (request: RetrievalRequest) => {
      return await aiService.retrieveSingle(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'retrieval', 'statistics'] })
    }
  })
}

/**
 * Custom hook to execute Retrieval Agent queries.
 */
export function useRetrievalAgent() {
  const queryClient = useQueryClient()
  return useMutation<RetrievalPackage, Error, RetrievalRequest>({
    mutationFn: async (request: RetrievalRequest) => {
      return await aiService.retrieveAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'retrieval', 'statistics'] })
    }
  })
}

/**
 * Custom hook to execute Retrieval Agent debug queries.
 */
export function useRetrievalAgentDebug() {
  const queryClient = useQueryClient()
  return useMutation<RetrievalPackage, Error, RetrievalRequest>({
    mutationFn: async (request: RetrievalRequest) => {
      return await aiService.retrieveAgentDebug(request)
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
 * Custom hook to monitor Retrieval Agent metrics statistics periodically.
 */
export function useRetrievalStatistics() {
  return useQuery<RetrievalAgentStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'retrieval', 'statistics'],
    queryFn: async () => {
      return await aiService.getRetrievalStatistics()
    },
    refetchInterval: 15000 // Refresh retrieval stats every 15 seconds
  })
}

/**
 * Custom hook to monitor raw retrieval metrics statistics periodically.
 */
export function useRetrievalStatisticsRaw() {
  return useQuery<RetrievalStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'retrieval', 'statistics', 'raw'],
    queryFn: async () => {
      return await aiService.getRetrievalStatisticsRaw()
    },
    refetchInterval: 15000 // Refresh retrieval stats every 15 seconds
  })
}

/**
 * Custom hook to execute context assembly prompts build.
 */
export function useBuildContext() {
  const queryClient = useQueryClient()
  return useMutation<ContextAssemblyResponse, Error, ContextAssemblyRequest>({
    mutationFn: async (request: ContextAssemblyRequest) => {
      return await aiService.buildContext(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'context', 'statistics'] })
    }
  })
}

/**
 * Custom hook to retrieve context assembly telemetry statistics periodically.
 */
export function useContextAssemblyStatistics() {
  return useQuery<ContextAssemblyStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'context', 'statistics'],
    queryFn: async () => {
      return await aiService.getContextAssemblyStatistics()
    },
    refetchInterval: 15000 // Refresh assembly stats every 15 seconds
  })
}

/**
 * Custom hook to monitor backend Graph compilation and health status periodically.
 */
export function useGraphHealth() {
  return useQuery<GraphHealthResponse, Error>({
    queryKey: ['admin', 'ai', 'graph', 'health'],
    queryFn: async () => {
      return await aiService.getGraphHealth()
    },
    refetchInterval: 10000, // Refresh health status check every 10 seconds
  })
}

/**
 * Custom hook to list all registered workflow nodes.
 */
export function useGraphNodes() {
  return useQuery<GraphNodesResponse, Error>({
    queryKey: ['admin', 'ai', 'graph', 'nodes'],
    queryFn: async () => {
      return await aiService.getGraphNodes()
    }
  })
}

/**
 * Custom hook to monitor graph execution performance statistics periodically.
 */
export function useGraphStatistics() {
  return useQuery<GraphStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'graph', 'statistics'],
    queryFn: async () => {
      return await aiService.getGraphStatistics()
    },
    refetchInterval: 10000, // Refresh stats check every 10 seconds
  })
}

/**
 * Custom hook to trigger mock execution run on the state graph.
 */
export function useGraphTestRun() {
  const queryClient = useQueryClient()
  return useMutation<GraphTestRunResponse, Error, GraphTestRunRequest>({
    mutationFn: async (request: GraphTestRunRequest) => {
      return await aiService.testGraphExecution(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'graph', 'statistics'] })
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'graph', 'health'] })
    }
  })
}

/**
 * Custom hook to fetch router mappings and active scoring rules configurations.
 */
export function useRouterIntents() {
  return useQuery<RouterIntentsResponse, Error>({
    queryKey: ['admin', 'ai', 'router', 'intents'],
    queryFn: async () => {
      return await aiService.getRouterIntents()
    }
  })
}

/**
 * Custom hook to run direct queries classification tests.
 */
export function useRouterClassify() {
  return useMutation<RouterClassifyResponse, Error, RouterClassifyRequest>({
    mutationFn: async (request: RouterClassifyRequest) => {
      return await aiService.classifyRouterQuery(request)
    }
  })
}

/**
 * Custom hook to run full state-graph routing roundtrip tests.
 */
export function useRouterTest() {
  const queryClient = useQueryClient()
  return useMutation<RouterTestResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testRouterPipeline(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'router', 'statistics'] })
    }
  })
}

/**
 * Custom hook to retrieve router statistics telemetry periodically.
 */
export function useRouterStatistics() {
  return useQuery<RouterStatisticsResponse, Error>({
    queryKey: ['admin', 'ai', 'router', 'statistics'],
    queryFn: async () => {
      return await aiService.getRouterStatistics()
    },
    refetchInterval: 10000, // Refresh stats check every 10 seconds
  })
}

/**
 * Custom hook to test the MedicalKnowledgeAgent RAG pipeline.
 */
export function useMedicalAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<MedicalKnowledgeAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testMedicalAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'core-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to test the SymptomAgent guidance pipeline.
 */
export function useSymptomAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<SymptomAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testSymptomAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'core-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to test the MemoryAgent memory pipeline.
 */
export function useMemoryAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<MemoryAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testMemoryAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'core-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to fetch core agents statistics periodically.
 */
export function useCoreAgentsStatistics() {
  return useQuery<Record<string, any>, Error>({
    queryKey: ['admin', 'ai', 'core-agents', 'statistics'],
    queryFn: async () => {
      return await aiService.getCoreAgentsStatistics()
    },
    refetchInterval: 10000, // Refresh metrics every 10 seconds
  })
}

/**
 * Custom hook to test the ReportAnalysisAgent.
 */
export function useReportAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<ReportAnalysisAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testReportAnalysisAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'healthcare-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to test the DrugInteractionAgent.
 */
export function useDrugAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<DrugInteractionAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testDrugInteractionAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'healthcare-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to test the DoctorRecommendationAgent.
 */
export function useDoctorAgentTest() {
  const queryClient = useQueryClient()
  return useMutation<DoctorRecommendationAgentResponse, Error, RouterTestRequest>({
    mutationFn: async (request: RouterTestRequest) => {
      return await aiService.testDoctorRecommendationAgent(request)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'ai', 'healthcare-agents', 'statistics'] })
    }
  })
}

/**
 * Custom hook to fetch healthcare agents statistics periodically.
 */
export function useHealthcareAgentsStatistics() {
  return useQuery<Record<string, any>, Error>({
    queryKey: ['admin', 'ai', 'healthcare-agents', 'statistics'],
    queryFn: async () => {
      return await aiService.getHealthcareAgentsStatistics()
    },
    refetchInterval: 10000, // Refresh metrics every 10 seconds
  })
}



